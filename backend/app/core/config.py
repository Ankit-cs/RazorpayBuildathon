import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "VERITY"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Razorpay Test Mode Credentials
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_mock_builder2026")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "sec_mock_builder_secret2026")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_mock_builder2026")
    
    # Merchant Profile
    MERCHANT_NAME: str = "NovaTech Gear (Razorpay Test Merchant)"
    MERCHANT_CATEGORY: str = "Electronics & Developer Gear"
    CURRENCY: str = "INR"

settings = Settings()
