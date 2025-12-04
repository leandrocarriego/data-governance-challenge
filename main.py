import os

if __name__ == "__main__":
    import uvicorn

    ENV = os.getenv("APP_ENV", "local")

    if ENV == "local":
        from pyngrok import ngrok

        ngrok.set_auth_token("36BG38mU2cM0AEYrt5sTThnaMwF_U9JCQ9ryUiXLnsYNoRnT")
        tunnel = ngrok.connect(8000, bind_tls=True)
        print("➡️  Ngrok Tunnel:", tunnel.public_url)

    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=(ENV == "local"),
    )

