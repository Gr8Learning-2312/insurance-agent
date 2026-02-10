## Run the Docker Image on your Instance

1.  **Install Docker on Instance**:
```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
sudo apt install git -y
```

2. **Pull the Docker Image from DockerHUB**
```bash
sudo docker pull gr8learning/insurance-agent:v1
```

3. **Verify the Docker Image**
```bash
sudo docker images
```

4. **Pass the OpenAI API Key and the Base URL and Run the Docker Image**
```bash
sudo docker run -d \
  --name insurance-agent \
  --restart unless-stopped \
  -e OPENAI_API_KEY=" < YOUR OPENAI API KEY > " \       
  -e OPENAI_BASE_URL=" < YOUR OPENAI BASE URL > " \
  -p 80:8501 \
  gr8learning/insurance-agent:v1

```