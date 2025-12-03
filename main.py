if __name__ == "__main__":
    from pyngrok import ngrok

    ngrok.set_auth_token("36BG38mU2cM0AEYrt5sTThnaMwF_U9JCQ9ryUiXLnsYNoRnT")

    public_url = ngrok.connect(8000, bind_tls=True)

    print(public_url)

    import uvicorn

    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)

