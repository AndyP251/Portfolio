import schedule
import time
import threading
from .views import pull_canvas_data

# def schedule_canvas_pull():
#     def run_continuously():
#         while True:
#             schedule.run_pending()
#             time.sleep(1)

#     schedule.every(24).hours.do(pull_canvas_data, canvas_api_url='your_canvas_api_url', access_token='your_access_token')
    
#     continuous_thread = threading.Thread(target=run_continuously)
#     continuous_thread.start()