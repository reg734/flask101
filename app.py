from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return  render_template('index.html')
#
# @app.route('/about')
# def about():
#     return render_template('about.html')
# @app.route('/')
# def show_weathers():
#     weather_list = ["sunny", "rainy", "cloudy", "sunny", "rainy"]
#     return render_template('weather.html', weather_list=weather_list)

if __name__ == '__main__':
    app.run()