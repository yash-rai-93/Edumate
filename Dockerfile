# 1. Use Python 3.10
FROM python:3.10-slim

# 2. Set up a non-root user (Required for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 3. Set Working Directory
WORKDIR /app

# 4. Copy Requirements & Install
# We copy with ownership set to 'user' so we can write files if needed
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy the Application Code
COPY --chown=user . .

# 6. Expose the Hugging Face Port
EXPOSE 7860

# 7. Start the App
CMD ["python", "app.py"]