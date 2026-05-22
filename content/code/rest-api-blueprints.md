---
title: "REST API Blueprints: Seven Production-Grade Implementations"
date: 2026-03-19
comments: true
---

**REST API Blueprints**: Seven production-ready REST API implementations across seven frameworks — FastAPI, Symfony, Laravel, NestJS, Spring Boot, Go/Gin, and Elixir/Phoenix — each with JWT auth, RBAC, AES-256 encryption, Domain-Driven Design, full CI, and AWS Terraform IaC.

## The Problem With "Hello World" APIs

Most REST API tutorials stop at the point where the interesting problems begin. You get routing and JSON responses. You don't get authentication that handles token refresh correctly. You don't get role-based access control that scales beyond two roles. You don't get infrastructure-as-code that actually provisions a production environment.

REST API Blueprints starts where those tutorials end.

## Seven Frameworks, One Standard

Each implementation satisfies the same specification:

- **Authentication**: JWT with access and refresh tokens, proper expiry handling
- **Authorization**: Role-Based Access Control (RBAC) with fine-grained permissions
- **Encryption**: AES-256 for sensitive fields at rest
- **Architecture**: Domain-Driven Design — entities, repositories, services, use cases
- **Security**: ISO 27001-aligned controls, input validation, rate limiting
- **CI/CD**: Full pipeline (lint, test, build, deploy)
- **Infrastructure**: AWS Terraform IaC (VPC, ECS, RDS, ALB)

The same spec, seven implementations. You can compare how each framework approaches the same problem, or use the one matching your stack as a starting template.

## The Frameworks

### FastAPI (Python)
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer

app = FastAPI()
security = HTTPBearer()

@app.get("/api/v1/users/me")
async def get_current_user(
    token: str = Depends(security),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.verify_token(token.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user.to_response()
```

FastAPI's dependency injection makes the auth pattern clean. The type annotations drive automatic OpenAPI documentation — your API spec is generated from your code, not maintained separately.

### Go / Gin
```go
func AuthMiddleware(userService *UserService) gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(401, gin.H{"error": "missing token"})
            return
        }
        user, err := userService.VerifyToken(strings.TrimPrefix(token, "Bearer "))
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
            return
        }
        c.Set("user", user)
        c.Next()
    }
}
```

The Go implementation is the most explicit — every step is visible. This verbosity is a feature when you need to understand exactly what your security middleware does.

### Elixir / Phoenix
```elixir
defmodule MyAppWeb.AuthController do
  use MyAppWeb, :controller
  alias MyApp.Auth

  def login(conn, %{"email" => email, "password" => password}) do
    case Auth.authenticate(email, password) do
      {:ok, user} ->
        token = Auth.generate_token(user)
        json(conn, %{token: token, user: UserView.render(user)})
      {:error, :invalid_credentials} ->
        conn |> put_status(401) |> json(%{error: "Invalid credentials"})
    end
  end
end
```

The pattern matching on `{:ok, user}` vs `{:error, reason}` is idiomatic Elixir — the error case is as visible as the success case, and neither requires exception handling.

## The Infrastructure Layer

Every blueprint includes Terraform that provisions a production-ready AWS environment:

```hcl
module "api" {
  source = "./modules/ecs-service"

  name          = "api"
  image         = var.api_image
  cpu           = 256
  memory        = 512
  desired_count = 2

  environment = {
    DATABASE_URL = module.rds.connection_string
    JWT_SECRET   = var.jwt_secret
  }

  target_group_arn = module.alb.target_group_arn
  subnet_ids       = module.vpc.private_subnet_ids
  security_groups  = [module.api_sg.id]
}
```

This isn't tutorial Terraform — it's production Terraform, with VPC isolation, private subnets, ALB for load balancing, RDS with automated backups, and ECS for container orchestration.

## ISO 27001 Alignment

The security controls in each implementation map to ISO 27001 domains:

| Control | Implementation |
|---------|----------------|
| A.9 — Access Control | RBAC with least-privilege roles |
| A.10 — Cryptography | AES-256 field encryption, bcrypt passwords |
| A.12 — Operations | Audit logging, rate limiting |
| A.14 — System Development | Input validation, SQL injection prevention |
| A.16 — Incident Management | Structured error responses, no stack traces in production |

The compliance alignment is not checkbox exercise — it shapes the architecture. RBAC that satisfies A.9 requires a permission model that's queryable, auditable, and can be updated without code changes.

## Using the Blueprints

Each framework lives in its own directory with a complete README, Docker Compose for local development, and the Terraform module for AWS:

```bash
git clone https://github.com/lucianofedericopereira/rest-api-blueprints
cd rest-api-blueprints/fastapi

docker compose up -d
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin"}'
```

## Links

- **GitHub**: [lucianofedericopereira/rest-api-blueprints](https://github.com/lucianofedericopereira/rest-api-blueprints)

## License

MIT
