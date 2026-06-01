FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy rest of frontend code
COPY . .

# Build Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Run the app
CMD ["npm", "start"]