import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

# গেটওয়ে রাউটার ইনিশিয়েট করা
gateway_router = APIRouter(prefix="/gateway", tags=["Network Gateway"])

# ব্যাকআপ এবং পাবলিক গেটওয়ে হোস্ট লিস্ট
FALLBACK_GATEWAYS = [
    "https://workers.cloudflare.com",
    "https://vercel.live",
    "https://pages.dev"
]

@gateway_router.get("/dns-check")
async def check_network_status(request: Request):
    """
    ইউজারের লোকাল নেটওয়ার্ক কানেকশন টেস্ট করার এন্ডপয়েন্ট।
    """
    return {
        "status": "online",
        "message": "Gateway Connection Successful",
        "client_ip": request.client.host if request.client else "Unknown",
        "suggested_gateways": FALLBACK_GATEWAYS
    }

@gateway_router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def reverse_proxy_gateway(request: Request, path: str):
    """
    রিভার্স প্রক্সি টানেল যা যেকোনো ব্লকড রিকোয়েস্টকে ব্যাকএন্ডে রি-রুট করে।
    """
    target_url = f"http://127.0.0.1:8000/{path}" 
    headers = dict(request.headers)
    headers.pop("host", None)
    
    async with httpx.AsyncClient() as client:
        try:
            content = await request.body()
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=content,
                timeout=12.0
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            return JSONResponse(
                status_code=502,
                content={"error": "Gateway Timeout", "details": str(e)}
            )
