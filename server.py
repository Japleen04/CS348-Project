from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import os

# from flask import Flask

# app = Flask(__name__)

# # members api route

# @app.route("/members")
# def members():
#     return {"members":["Member1", "Member2", "Member3"]}

# if __name__ == "__main__":
#     app.run(debug=True, port=5001)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'  # Use SQLite for simplicity
db = SQLAlchemy(app)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer)  # minutes
    cook_time = db.Column(db.Integer)  # minutes
    servings = db.Column(db.Integer)
    category = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Recipe {self.title}>'
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "servings": self.servings,
            "category": self.category
        }
    
@app.route("/")
def index():
    return render_template("index.html")

# @app.route("/members")
# def members():
#     return {"members": ["Member1", "Member2", "Member3"]}

@app.route("/recipes", methods=["POST"])
def add_recipe():
    data = request.get_json()
    new_recipe = Recipe(
        title=data['title'],
        ingredients=data['ingredients'],
        instructions=data['instructions'],
        prep_time=data.get('prep_time'),
        cook_time=data.get('cook_time'),
        servings=data.get('servings'),
        category=data.get('category')
    )
    db.session.add(new_recipe)
    db.session.commit()
    return {"message": "Recipe added!"}, 201

# @app.route("/recipes", methods=["GET"])
# def get_recipes():
#     recipes = Recipe.query.all()
#     return {"recipes": [recipe.to_dict() for recipe in recipes]}, 200

@app.route("/recipes", methods=["GET"])
def get_recipes():
    category = request.args.get('category')
    if category:
        recipes = Recipe.query.filter_by(category=category).all()
    else:
        recipes = Recipe.query.all()
    return {"recipes": [recipe.to_dict() for recipe in recipes]}, 200

@app.route("/recipes/<int:id>", methods=["GET"])
def get_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    return recipe.to_dict(), 200

@app.route("/recipes/<int:id>", methods=["PUT"])
def update_recipe(id):
    data = request.get_json()
    recipe = Recipe.query.get_or_404(id)
    recipe.title = data['title']
    recipe.ingredients = data['ingredients']
    recipe.instructions = data['instructions']
    recipe.prep_time = data.get('prep_time')
    recipe.cook_time = data.get('cook_time')
    recipe.servings = data.get('servings')
    recipe.category = data.get('category')
    db.session.commit()
    return {"message": "Recipe updated!"}, 200

@app.route("/recipes/<int:id>", methods=["DELETE"])
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    db.session.delete(recipe)
    db.session.commit()
    return {"message": "Recipe deleted!"}, 200

# # New route with prepared statement
# @app.route("/recipes/report", methods=["GET"])
# def get_recipe_report():
#     search_term = request.args.get("term", "%")  # Default to "%" to fetch all if no term provided
#     # Use a raw SQL query with a prepared statement for safe parameterized queries
#     sql = "SELECT title, ingredients FROM recipe WHERE title LIKE :search_term"
#     result = db.session.execute(sql, {"search_term": f"%{search_term}%"}).fetchall()

#     report = [{"title": row[0], "ingredients": row[1]} for row in result]
#     return {"report": report}, 200


# New route with prepared statement
@app.route("/recipes/report", methods=["GET"])
def get_recipe_report():
    category = request.args.get("category", None)
    
    if category:
        sql = text("""
                SELECT COUNT(*) AS count, 
                   AVG(prep_time) AS avg_prep_time, 
                   AVG(cook_time) AS avg_cook_time, 
                   AVG(servings) AS avg_servings, 
                   MAX(prep_time + cook_time) AS max_total_time,
                   MIN(prep_time + cook_time) AS min_total_time 
                FROM recipe 
                WHERE category = :category
                """)
        # sql = "SELECT COUNT(*) FROM recipe WHERE category = :category"
        result = db.session.execute(sql, {"category": category}).fetchone()
        report = {

            "category": category, 
            "count": result[0], 
            "avg_prep_time": result[1], 
            "avg_cook_time": result[2], 
            "avg_servings": result[3],
            "max_total_time": result[4],
            "min_total_time": result[5]
        }
    else:
        report = {"message": "Please specify a category to generate the report."}
    return report, 200

@app.route("/categories", methods=["GET"])
def get_categories():
    categories = db.session.query(Recipe.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return {"categories": categories}, 200

# @app.before_first_request
def create_indexes():
    with app.app_context():
        connection = db.engine.connect()
        connection.execute(text('CREATE INDEX IF NOT EXISTS idx_category ON recipe (category);'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS idx_title ON recipe (title);'))


if __name__ == "__main__":
    with app.app_context():  # Create application context
        db.create_all()  # Create the database and tables
        create_indexes() # Create indexes
    app.run(debug=True, port=5001)
