from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes_catalog import router as catalog_router
from .api.routes_agent import router as agent_router
from .api.routes_webhook import router as webhook_router
from .api.routes_mcp import router as mcp_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Agent-Readable Storefront & Bounded Checkout Agent on Razorpay Rails"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router, prefix=settings.API_PREFIX)
app.include_router(agent_router, prefix=settings.API_PREFIX)
app.include_router(webhook_router, prefix=settings.API_PREFIX)
app.include_router(mcp_router, prefix=settings.API_PREFIX)

from .api.routes_projectx import router as projectx_router
app.include_router(projectx_router)

@app.get("/")
def root_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "merchant": settings.MERCHANT_NAME,
        "razorpay_mode": "Live Test Key" if not settings.RAZORPAY_KEY_ID.startswith("rzp_test_mock") else "Test Simulator Active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
