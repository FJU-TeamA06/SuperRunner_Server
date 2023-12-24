from flask import Flask, request, jsonify
import mysql.connector.pooling
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)

# 連線參數
db_config = {
    'user': os.getenv('DB_USER'), 
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_DATABASE'),
    'pool_name': os.getenv('DB_POOL_NAME'),
    'pool_size': int(os.getenv('DB_POOL_SIZE'))
}

# Initialize connection pool
pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def get_db_connection():
    """Get a database connection from the pool."""
    return pool.get_connection()

@app.route('/players')
def get_players():
    mode = request.args.get('mode')
    pname = request.args.get('pname')
    sname = request.args.get('sname')
    cnx = None
    cursor = None
    try:
            cnx = get_db_connection()
            cursor = cnx.cursor()

            if mode == 'getorderplayers':
                query = "SELECT distinct PlayerName, PlayerScore FROM players WHERE PlayerSession = %s ORDER BY PlayerScore DESC"
                cursor.execute(query, (sname,))
                result = cursor.fetchall()
                players = [{'name': r[0], 'score': r[1]} for r in result]
                return jsonify(players)
            if mode == 'getsessionplayers':
              
              sname = request.args.get('sname')

              # 查詢語句 
              query = "SELECT distinct PlayerName,PlayerScore FROM players WHERE PlayerSession = %s"
              cursor.execute(query, (sname,))
              
              # 獲取並返回結果
              result = cursor.fetchall()
              return jsonify(result)
            if mode == 'clearsession':

                sname = request.args.get('sname')

                # 刪除語句
                query = "DELETE FROM players WHERE PlayerSession = %s" 
                cursor.execute(query, (sname,))

                # 提交事務
                cnx.commit()

                return "Session players cleared"
            if mode == 'resetscore':

              sname = request.args.get('sname')

              # 更新語句  
              query = "UPDATE players SET PlayerScore = 0 WHERE PlayerSession = %s"
              cursor.execute(query, (sname,))

              # 提交事務
              cnx.commit() 


              return "Player scores reset"

            if mode == 'addplayerscore':

              sname = request.args.get('sname') 
              pname = request.args.get('pname')
              score = request.args.get('score') 

              # 更新語句
              query = "UPDATE players SET PlayerScore = PlayerScore + %s WHERE PlayerName = %s AND PlayerSession = %s"
              cursor.execute(query, (score, pname, sname))

              # 提交事務
              cnx.commit()

              # 查詢並返回結果
              query = "SELECT * FROM players WHERE PlayerName = %s AND PlayerSession = %s" 
              cursor.execute(query, (pname, sname))
              result = cursor.fetchone()
              return jsonify(result)
            if mode == 'setplayerdata':

              pname = request.args.get('pname')
              sname = request.args.get('sname') 
              score = request.args.get('score')

               # 查詢是否已存在
              query = "SELECT * FROM players WHERE PlayerName = %s AND PlayerSession = %s"
              cursor.execute(query, (pname, sname))
              result = cursor.fetchone()

         
              # 執行插入
              query = "INSERT INTO players (PlayerName, PlayerSession, PlayerScore) VALUES (%s, %s, %s)"
              cursor.execute(query, (pname, sname, score))  
              cnx.commit()

              # 插入後,查詢返回結果
              query = "SELECT * FROM players WHERE PlayerName = %s AND PlayerSession = %s"
              cursor.execute(query, (pname, sname)) 
              result = cursor.fetchone()
              return jsonify(result)
                

            # 其他處理程式碼    
            else:
              if pname and sname:

                # 查詢語句
                query = "SELECT * FROM players WHERE PlayerName=%s AND PlayerSession=%s"
                cursor.execute(query, (pname, sname))

                # 取得並返回結果
                result = cursor.fetchone()  
                results = [result]
                return jsonify(results)

              # 原來的處理程式碼
              else:
                if mode == 'getalldata':

                    # 查詢語句
                    query = ("SELECT * FROM players LIMIT 1000")

                    # 執行查詢
                    cursor.execute(query)  

                    # 取得資料
                    results = cursor.fetchall()

                    return jsonify(results)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
    finally:
      if cursor:  
        if cursor.with_rows:
          cursor.fetchall()
        cursor.close()
      if cnx:
        cnx.close()
@app.route('/leaderboard')
def get_leaderboard():
  mode=request.args.get('mode')
  try:
    cnx = get_db_connection()
    cursor = cnx.cursor()
    if(mode=='resetleaderscore'):
      reset_leaderboard('day');
      reset_leaderboard('week');
      reset_leaderboard('month');
      query=("SELECT * FROM leaderboard LIMIT 1000")
          # 執行查詢
      cursor.execute(query)  
            # 取得資料
      results = cursor.fetchall()

      return jsonify(results)
    if(mode=='getleaderscore'):
      query=("SELECT * FROM leaderboard LIMIT 1000")
          # 執行查詢
      cursor.execute(query)  
            # 取得資料
      results = cursor.fetchall()

      return jsonify(results)
    if(mode=='updateleaderscore'):
      pname = request.args.get('pname')
      score = request.args.get('score') 
      # Retrieve the current high scores from the leaderboard
      query = "SELECT type, playerName, score FROM leaderboard"
      cursor.execute(query)
      current_scores = cursor.fetchall()
      
      # Create a dictionary for easy score type lookup
      score_types = {score[0]: score[2] for score in current_scores}
      
      # Prepare the update query
      update_query = "UPDATE leaderboard SET playerName = %s, score = %s WHERE type = %s"
      
      # Check and update for each score type if necessary
      for score_type in ['day', 'week', 'month']:
          if int(score) > score_types[score_type]:
              cursor.execute(update_query, (pname, score, score_type))
      
      # Commit the updates
      cnx.commit()
      
      return "Leaderboard updated successfully"
  except Exception as e:
      print(f"An error occurred: {e}")
      return jsonify({"error": "An internal error occurred"}), 500
  finally:
      cursor.close()
      cnx.close()
def reset_leaderboard(type):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        
        # The SQL query to reset the score
        query = "UPDATE leaderboard SET playerName = '尚無玩家', score = 0 WHERE type = %s"
        cursor.execute(query, (type,))
        cnx.commit()
    except Exception as e:
        print(f"An error occurred while resetting leaderboard: {e}")
    finally:
        cursor.close()
        cnx.close()

# Function to schedule the resets
def schedule_resets():
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Taipei'))

    # Schedule daily reset at midnight
    scheduler.add_job(reset_leaderboard, 'cron', hour=0, minute=0, args=['day'])

    # Schedule weekly reset at Monday midnight
    scheduler.add_job(reset_leaderboard, 'cron', day_of_week='mon', hour=0, minute=0, args=['week'])

    # Schedule monthly reset on the first of the month at midnight
    scheduler.add_job(reset_leaderboard, 'cron', day=1, hour=0, minute=0, args=['month'])

    scheduler.start()

if __name__ == '__main__':
    app.debug = True
    schedule_resets()
    app.run('0.0.0.0')