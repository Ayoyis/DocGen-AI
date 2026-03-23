# app/main.py
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from contextlib import asynccontextmanager
from typing import List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .retriever import CodeBERTRetriever
from .generator import (
    CodeT5Generator,
    identify_lines_needing_comments,
    generate_template_docstring,
)
from .parser import extract_blocks, CodeBlock

# Evaluation imports
from .evaluation import DocGenEvaluator
from .test_data import TestDataManager, QUICK_TEST_SAMPLES
import tempfile

from .database import init_db, get_db, User, get_password_hash, verify_password
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta

from fastapi import Depends
from fastapi import Form
from fastapi.responses import RedirectResponse
import secrets

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")


# Global model references
retriever: Optional[CodeBERTRetriever] = None
generator: Optional[CodeT5Generator] = None


# Lifespan (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever, generator

    init_db()  # Create tables

    # Validate FAISS paths before loading models
    warning_list = settings.validate_paths(raise_on_missing=False)
    for w in warning_list:
        print(f"[Config] WARNING: {w}")

    print("Loading models...")
    retriever = CodeBERTRetriever(
        model_name=settings.codebert_model,
        index_path=str(settings.index_path),
        meta_path=str(settings.meta_path),
        device=settings.device,
    )
    
    generator = CodeT5Generator(
        model_name=settings.codet5_model,
        device=settings.device,
    )
    print("Models loaded successfully.")
    yield

    # Cleanup on shutdown
    retriever = None
    generator = None


# FastAPI App
app = FastAPI(
    title="AI Code Comment & Documentation Generator",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "cors_origins", ["http://localhost:3000"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class GenerateRequest(BaseModel):
    language: str = Field(default="python")
    code: str
    top_k: int = Field(default=3, ge=0, le=8)
    generate_inline: bool = Field(default=True, description="Generate inline comments")
    generate_docstrings: bool = Field(default=True, description="Generate docstrings")


class BlockResult(BaseModel):
    name: str
    type: str
    original_code: str
    commented_code: str
    documentation: str
    start_line: int
    end_line: int


class GenerateResponse(BaseModel):
    blocks: List[BlockResult]
    full_commented_code: str
    language: str


# Evaluation models
class EvaluateRequest(BaseModel):
    test_set: str = "test_set.jsonl"
    use_retrieval: bool = True
    max_samples: Optional[int] = None


class CompareRequest(BaseModel):
    test_set: str = "test_set.jsonl"
    max_samples: Optional[int] = 50


# Utility Functions
def add_comments_to_code(
    code: str,
    comments: List[Tuple[int, str]],
    language: str,
) -> str:
    """O(n) comment insertion using dict lookup."""
    lines = code.split("\n")
    result_lines: List[str] = []
    comment_map: dict[int, str] = {line_num: comment for line_num, comment in comments}

    for i, line in enumerate(lines, 1):
        if i in comment_map:
            indent_len = len(line) - len(line.lstrip())
            indentation = line[:indent_len]
            result_lines.append(indentation + comment_map[i])
        result_lines.append(line)

    return "\n".join(result_lines)


def reassemble_code(
    original_code: str,
    results: List[BlockResult],
    language: str,
) -> str:
    """Rebuild full source file preserving imports and module-level code."""
    if not results:
        return original_code

    original_lines = original_code.split("\n")
    total_lines = len(original_lines)
    sorted_results = sorted(results, key=lambda r: r.start_line)

    output_lines: List[str] = []
    current_line = 1

    for block in sorted_results:
        if current_line < block.start_line:
            output_lines.extend(
                original_lines[current_line - 1 : block.start_line - 1]
            )
        output_lines.extend(block.commented_code.split("\n"))
        current_line = block.end_line + 1

    if current_line <= total_lines:
        output_lines.extend(original_lines[current_line - 1 :])

    return "\n".join(output_lines)


def process_single_block(
    block: CodeBlock,
    language: str,
    top_k: int,
    generate_inline: bool = True,
    generate_docstrings: bool = True,
) -> BlockResult:
    """Process one code block: add inline comments and/or generate docstring."""

    if generate_inline:
        comments_needed = identify_lines_needing_comments(block.code, language)
        commented_code = add_comments_to_code(block.code, comments_needed, language)
        print(f"[{block.name}] Inline comments: {[c[1] for c in comments_needed]}")
    else:
        commented_code = block.code
        print(f"[{block.name}] Inline comments skipped.")

    if generate_docstrings:
        if block.type in ('function', 'class', 'method'):
            documentation = generate_template_docstring(block.code, block.name, language)
            print(f"[{block.name}] Template docstring generated.")
        elif block.type == 'module' and generator is not None:
            documentation = generator.generate_module_docstring(block.code, language)
            print(f"[{block.name}] CodeT5 module docstring generated.")
        else:
            documentation = ""
            print(f"[{block.name}] Docstring skipped.")
    else:
        documentation = ""
        print(f"[{block.name}] Docstring skipped.")

    return BlockResult(
        name=block.name,
        type=block.type,
        original_code=block.code,
        commented_code=commented_code,
        documentation=documentation,
        start_line=block.start_line,
        end_line=block.end_line,
    )


# Endpoints - Health & Generation
@app.get("/health")
def health():
    return {
        "status": "ok",
        "models_loaded": retriever is not None and generator is not None,
        "device": "cpu",
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """Main generation endpoint."""
    try:
        blocks = extract_blocks(req.code, req.language)
        print(f"\nFound {len(blocks)} block(s): {[b.name for b in blocks]}")

        if not blocks:
            return GenerateResponse(
                blocks=[],
                full_commented_code=req.code,
                language=req.language,
            )

        results = [
            process_single_block(
                block,
                req.language,
                req.top_k,
                generate_inline=req.generate_inline,
                generate_docstrings=req.generate_docstrings,
            )
            for block in blocks
        ]

        full_commented = reassemble_code(req.code, results, req.language)

        preview = (
            full_commented[:500] + "..."
            if len(full_commented) > 500
            else full_commented
        )
        print(f"\n=== OUTPUT ({len(full_commented)} chars) ===\n{preview}\n=== END ===\n")

        return GenerateResponse(
            blocks=results,
            full_commented_code=full_commented,
            language=req.language,
        )

    except Exception as e:
        print(f"Error in /generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/comment")
def comment_legacy(req: GenerateRequest):
    """Legacy endpoint for backward compatibility."""
    response = generate(req)
    first_block = response.blocks[0] if response.blocks else None
    return {
        "docstring": first_block.documentation if first_block else "",
        "commented_code": response.full_commented_code,
        "blocks": len(response.blocks),
    }


# Endpoints - Evaluation
@app.post("/evaluate")
async def run_evaluation(req: EvaluateRequest):
    """
    Run automated evaluation on test set.
    
    Example:
    {
        "test_set": "test_set.jsonl",
        "use_retrieval": true,
        "max_samples": 10
    }
    """
    try:
        if generator is None:
            raise HTTPException(status_code=503, detail="Models not loaded")

        data_manager = TestDataManager()
        test_data = data_manager.load(req.test_set)
        
        if req.max_samples:
            test_data = test_data[:req.max_samples]
        
        evaluator = DocGenEvaluator(generator, retriever)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report = evaluator.evaluate_batch(
                test_data, 
                use_retrieval=req.use_retrieval,
                save_path=tmpdir
            )
        
        return {"status": "success", "report": report}
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Test set not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate/quick")
async def quick_evaluation():
    """Quick evaluation on 3 sample examples."""
    if generator is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    evaluator = DocGenEvaluator(generator, retriever)
    
    results = []
    for sample in QUICK_TEST_SAMPLES:
        result = evaluator.evaluate_sample(sample, use_retrieval=True)
        results.append(result.to_dict())
    
    return {
        "status": "success",
        "samples_evaluated": len(results),
        "results": results
    }


@app.post("/evaluate/compare")
async def compare_modes(req: CompareRequest):
    """Compare RAG vs non-RAG performance."""
    if generator is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    data_manager = TestDataManager()
    test_data = data_manager.load(req.test_set)
    
    if req.max_samples:
        test_data = test_data[:req.max_samples]
    
    evaluator = DocGenEvaluator(generator, retriever)
    
    # With RAG
    report_rag = evaluator.evaluate_batch(test_data, use_retrieval=True, save_path=None)
    
    # Without RAG
    report_no_rag = evaluator.evaluate_batch(test_data, use_retrieval=False, save_path=None)
    
    return {
        "status": "success",
        "with_rag": {
            "bleu": report_rag['metrics']['bleu']['mean'],
            "rougeL": report_rag['metrics']['rougeL']['mean'],
            "meteor": report_rag['metrics']['meteor']['mean'],  # ADD THIS
            "avg_time_ms": report_rag['performance']['avg_generation_time_ms']
        },
        "without_rag": {
            "bleu": report_no_rag['metrics']['bleu']['mean'],
            "rougeL": report_no_rag['metrics']['rougeL']['mean'],
            "meteor": report_no_rag['metrics']['meteor']['mean'],  # ADD THIS
            "avg_time_ms": report_no_rag['performance']['avg_generation_time_ms']
        },
        "improvement": {
            "bleu": round(report_rag['metrics']['bleu']['mean'] - report_no_rag['metrics']['bleu']['mean'], 4),
            "rougeL": round(report_rag['metrics']['rougeL']['mean'] - report_no_rag['metrics']['rougeL']['mean'], 4),
            "meteor": round(report_rag['metrics']['meteor']['mean'] - report_no_rag['metrics']['meteor']['mean'], 4)  # ADD THIS
        }
    }


@app.get("/evaluation/datasets")
async def list_datasets():
    """List available test datasets."""
    data_manager = TestDataManager()
    datasets = list(data_manager.data_dir.glob("*.jsonl"))
    
    return {
        "datasets": [
            {
                "name": d.name,
                "stats": data_manager.get_stats(d.name)
            }
            for d in datasets
        ]
    }


@app.post("/evaluation/datasets/create-quick")
async def create_quick_test_set():
    """Create a small test set for quick testing."""
    data_manager = TestDataManager()
    path = data_manager.create_manual_test_set(QUICK_TEST_SAMPLES, "quick_test.jsonl")
    return {"created": path, "samples": len(QUICK_TEST_SAMPLES)}

# Auth endpoints
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

@app.post("/auth/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=data.email,
        name=data.name,
        hashed_password=get_password_hash(data.password)
    )
    db.add(user)
    db.commit()
    return {"message": "User created"}


@app.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode(
        {"sub": email, "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256"
    )
    return {"access_token": token, "token_type": "bearer", "name": user.name}


# GitHub OAuth (FREE - no cost)
@app.get("/auth/github")
def github_login():
    """Redirect to GitHub OAuth"""
    client_id = GITHUB_CLIENT_ID  # Get from GitHub Settings > Developer > OAuth Apps
    redirect_uri = "http://localhost:8000/auth/github/callback"
    scope = "read:user user:email"
    
    github_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
    return RedirectResponse(github_url)

@app.get("/auth/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback"""
    import httpx
    
    # Exchange code for token
    client_id = GITHUB_CLIENT_ID
    client_secret = GITHUB_CLIENT_SECRET
    
    token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        },
    )
    token_data = token_res.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub auth failed")
    
    # Get user info
    user_res = httpx.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {access_token}"},
    )
    user_data = user_res.json()
    
    email = user_data.get("email") or f"{user_data['id']}@github.com"
    name = user_data.get("name") or user_data.get("login")
    
    # Create or get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(secrets.token_urlsafe(32))  # Random password
        )
        db.add(user)
        db.commit()
    
    # Create session token
    token = jwt.encode(
        {"sub": email, "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256"
    )
    
    # Redirect to frontend with token
    return RedirectResponse(f"https://docgen-ai.vercel.app/auth/callback?token={token}")

# Google OAuth (FREE - no cost for basic usage)
@app.get("/auth/google")
def google_login():
    """Redirect to Google OAuth"""
    client_id = GOOGLE_CLIENT_ID  # Get from Google Cloud Console
    redirect_uri = "http://localhost:8000/auth/google/callback"
    scope = "openid email profile"
    
    google_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
    return RedirectResponse(google_url)

@app.get("/auth/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    import httpx
    
    # Exchange code for token
    token_res = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": "http://localhost:8000/auth/google/callback",
            "grant_type": "authorization_code",
        },
    )
    token_data = token_res.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Google auth failed")
    
    # Get user info
    user_res = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user_data = user_res.json()
    
    email = user_data["email"]
    name = user_data.get("name", email.split("@")[0])
    
    # Create or get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(secrets.token_urlsafe(32))
        )
        db.add(user)
        db.commit()
    
    token = jwt.encode(
        {"sub": email, "exp": datetime.utcnow() + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256"
    )
    
    return RedirectResponse(f"http://localhost:3000/auth/callback?token={token}")

#Forgot Password
# Email config - use your email credentials
mail_config = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_USERNAME,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

@app.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    
    # Always return success even if email not found (security best practice)
    if not user:
        return {"message": "If that email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token on user (add these columns to your User model)
    user.reset_token = reset_token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send email
    reset_url = f"[localhost](http://localhost:3000/reset-password?token={reset_token})"
    message = MessageSchema(
        subject="Reset your password",
        recipients=[data.email],
        body=f"Click this link to reset your password: {reset_url}\n\nThis link expires in 1 hour.",
        subtype="plain"
    )
    
    fm = FastMail(mail_config)
    await fm.send_message(message)
    
    return {"message": "If that email exists, a reset link has been sent"}


@app.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == data.token).first()
    
    if not user or user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user.hashed_password = get_password_hash(data.password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    
    return {"message": "Password reset successfully"}
