# まず、ファイルに実行権限を付与します
chmod +x setup.sh

# ファイルのあるディレクトリでセットアップを実行します
./setup.sh

# 以下のコマンドを順に実行してください
source venv/bin/activate
pip uninstall opencv-python -y
pip install opencv-python-headless==4.12.0.88



# プレイリストから開始（全画面表示）
./run.sh start playlist.csv
# 単一ファイルを再生（ウィンドウ表示、プレイリストを続行）
./run.sh play "test/2.jpg" 3
# ビデオプレーヤーを強制停止
./run.sh stop
# PyQt5 環境を終了
./run.sh exit
