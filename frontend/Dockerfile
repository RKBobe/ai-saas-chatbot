FROM node:18-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

# Expose port 5173 for Vite
EXPOSE 5173

# Command to run the application in development mode
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
