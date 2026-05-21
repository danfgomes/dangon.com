from fastapi import FastAPI
from schemas import User, User_response, UserUpdate, UserDeleteResponse, Post, PostResponse, PostDeleteResponse, UpdatePost
from fastapi import HTTPException

app = FastAPI()

banco_de_dados = []
lista_de_post = []


@app.get("/")
def read_root():
        return {"bem vindo": "my api"}

@app.post("/users", response_model=User_response)
async def create_user(dados_do_usuario: User):
    banco_de_dados.append(dados_do_usuario)

    resposta = dados_do_usuario.model_dump()
    resposta["message"] = "created user successfully"
    return resposta

@app.get("/users", response_model=list[User])
def get_users():
    return banco_de_dados

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    for user in banco_de_dados:
        if user.id == user_id:
            return user

    raise HTTPException(
        status_code=404,
        detail="User not found"
     )

@app.patch("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate):
    for user in banco_de_dados:
        if user.id == user_id:
            if user_update.name is not None:
                user.name = user_update.name
            if user_update.email is not None:
                user.email = user_update.email
            return user

    raise HTTPException(
        status_code=404,
        detail="User not found"
     )

@app.delete("/users/{user_id}", response_model=UserDeleteResponse)
async def delete_user(user_id: int):
    for user in banco_de_dados:
        if user.id == user_id:
            banco_de_dados.remove(user)
            return {"message": "User deleted successfully"}

    raise HTTPException(
        status_code=404,
        detail="User not found"
     )

@app.post("/posts", response_model=PostResponse)
async def create_post(post: Post):
    lista_de_post.append(post)
    resposta = post.model_dump()
    resposta["message"] = "Post created successfully"
    return resposta

@app.get("/posts", response_model=list[Post])
def get_posts():
    return lista_de_post

@app.get("/posts/{post_id}", response_model=Post)
def get_post(post_id: int):
    for post in lista_de_post:
        if post.id == post_id:
            return post
    raise HTTPException(
        status_code=404,
        detail="Post not found"
    )

@app.delete("/posts/{post_id}", response_model=PostDeleteResponse)
async def delete_post(post_id: int):
    for post in lista_de_post:
        if post.id == post_id:
            lista_de_post.remove(post)
            return {"message": "Post deleted successfully"}

    raise HTTPException(
        status_code=404,
        detail="Post not found"
     )

@app.patch("/posts/{post_id}", response_model=Post)
async def update_post(post_id: int, post_update: UpdatePost):
    for post in lista_de_post:
        if post.id == post_id:
            if post_update.title is not None:
                post.title = post_update.title
            if post_update.content is not None:
                post.content = post_update.content
            return post

    raise HTTPException(
        status_code=404,
        detail="Post not found"
     )


