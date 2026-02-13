FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .

# Create .env file for React to pick up (connect to local MuleSoft backend)
RUN echo "REACT_APP_API_URL=http://localhost:4797/api" > .env && \
    echo "REACT_APP_BACKEND_URL=http://localhost:4797/api" >> .env

EXPOSE 3000
CMD ["npm", "start"]
