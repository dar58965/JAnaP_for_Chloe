
from controllers import app
from controllers import configuration

from flask import render_template
from flask import redirect

@app.route("/")
def getHome():
    return redirect("/projects")
