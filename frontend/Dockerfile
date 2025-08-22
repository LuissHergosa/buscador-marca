# Use Bun image for development
FROM oven/bun:1
WORKDIR /app

# Install dependencies
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Expose port
EXPOSE 80

# Start development server
CMD ["bun", "run", "dev", "--host", "0.0.0.0", "--port", "80"]
