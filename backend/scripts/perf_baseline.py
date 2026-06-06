"""
Performance baseline measurement. Run from backend/ with server running:
  .venv/bin/python scripts/perf_baseline.py
"""
import asyncio
import time
import httpx

BASE_URL = "http://localhost:8000"
ITERATIONS = 20


async def measure(client: httpx.AsyncClient, method: str, path: str, **kwargs) -> float:
    times = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        response = await client.request(method, f"{BASE_URL}{path}", **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        assert response.status_code < 500, f"Server error on {path}: {response.text}"
    avg = sum(times) / len(times)
    p95 = sorted(times)[int(ITERATIONS * 0.95)]
    return avg, p95


async def main():
    # Register and login to get a token
    async with httpx.AsyncClient() as client:
        email = f"perf_{int(time.time())}@test.com"
        await client.post(f"{BASE_URL}/auth/register", json={"email": email, "password": "perf1234!"})
        form = {"username": email, "password": "perf1234!"}
        resp = await client.post(f"{BASE_URL}/auth/jwt/login", data=form)
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print(f"\n{'Endpoint':<40} {'Avg (ms)':>10} {'P95 (ms)':>10}")
        print("-" * 62)

        for label, method, path, kw in [
            ("GET /exercises/", "GET", "/exercises/", {}),
            ("GET /exercises/?name=squat", "GET", "/exercises/?name=squat", {}),
            ("GET /exercises/?muscle_groups=chest", "GET", "/exercises/?muscle_groups=chest", {}),
            ("GET /workouts/", "GET", "/workouts/", {"headers": headers}),
        ]:
            avg, p95 = await measure(client, method, path, **kw)
            print(f"{label:<40} {avg:>10.1f} {p95:>10.1f}")

if __name__ == "__main__":
    asyncio.run(main())
