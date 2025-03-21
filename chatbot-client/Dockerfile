FROM docker.io/library/node:20-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM docker.io/library/node:20-bookworm-slim AS prod
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist /app/dist
EXPOSE 3000
ENTRYPOINT ["serve", "-s", "dist", "-l", "3000"]

