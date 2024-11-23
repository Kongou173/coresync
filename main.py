import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
import pytz
from datetime import datetime, timedelta
import asyncio
import random
from keep_alive import keep_alive
from gemini_chat import gemini_chat
from dotenv import load_dotenv
import wikipedia

# 環境変数の読み込み
load_dotenv("./lol/.env")

# 環境変数の取得
TOKEN = os.getenv("DISCORD_TOKEN")
SUPPORT_SERVER_URL = os.getenv("SUPPORT_SERVER_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Botの初期設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # banやkickで必要

bot = commands.Bot(command_prefix="!", intents=intents)
synced = False  # コマンドの同期フラグ

# 会話履歴を保存する変数（グローバルに設定）
conversation_history = []

# ステータス表示（presence）
@tasks.loop(seconds=20)
async def presence_loop():
    game = discord.Game("/help - Bot Help")
    await bot.change_presence(activity=game)

# Bot起動時の処理
@bot.event
async def on_ready():
    global synced
    if not synced:
        await bot.tree.sync()  # スラッシュコマンドの同期
        synced = True
    print(f"Logged in as {bot.user.name}")
    presence_loop.start()

# /help コマンド：利用可能なコマンド一覧を表示
@bot.tree.command(name="help", description="利用可能なコマンド一覧を表示します")
async def bot_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ボットの使い方",
        color=discord.Colour.blurple()
    ).add_field(name="/help", value="利用可能なコマンド一覧を表示します") \
     .add_field(name="/ban <user>", value="ユーザーをBANします") \
     .add_field(name="/kick <user>", value="ユーザーをキックします") \
     .add_field(name="/timeout <user> <duration>", value="指定された時間だけユーザーをタイムアウトします (1分〜1時間)") \p
     .add_field(name="/support", value="サポートサーバーのリンクを表示します") \
     .add_field(name="/say <message>", value="Botが指定メッセージを代わりに話します") \
     .add_field(name="/time", value="現在の時刻を表示します") \
     .add_field(name="/chat <message>", value="Gemini APIとチャット") \
     .add_field(name="/chat_clear", value="チャット履歴を削除します") \
     .add_field(name="/random", value="ユーザー名をランダムに変更します")
　　　.add_field(name="/wiki", value="Wikipediaから情報を取得します")
　　　.add_field(name="/server", value="サーバー情報を取得します")
    await interaction.response.send_message(embed=embed)

        title="サポートサーバーリンク",
        description=SUPPORT_SERVER_URL, # 直接リンクを表示
        color=discord.Colour.blue()  # 埋め込みの色を設定
    )
    await interaction.response.send_message(embed=embed)




# /ban コマンド：ユーザーをBAN
@bot.tree.command(name="ban", description="ユーザーをBANします")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if interaction.user.guild_permissions.ban_members:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} をBANしました。")
    else:
        await interaction.response.send_message("BAN権限がありません。", ephemeral=True)

# /kick コマンド：ユーザーをキック
@bot.tree.command(name="kick", description="ユーザーをキックします")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if interaction.user.guild_permissions.kick_members:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} をキックしました。")
    else:
        await interaction.response.send_message("キック権限がありません。", ephemeral=True)

timeout コマンド：ユーザーをタイムアウト
@bot.tree.command(name="timeout", description="指定時間だけユーザーをタイムアウトします")
async def timeout(interaction: discord.Interaction, member: discord.Member, duration: int):
    if interaction.user.guild_permissions.moderate_members:
        if 1 <= duration <= 60:
            timeout_duration = discord.utils.utcnow() + timedelta(minutes=duration)
            await member.timeout(timeout_duration)
            await interaction.response.send_message(f"{member.mention} を {duration} 分間タイムアウトしました。")
        else:
            await interaction.response.send_message("タイムアウトの時間は1分〜60分の範囲で指定してください。", ephemeral=True)
    else:
        await interaction.response.send_message("タイムアウト権限がありません。", ephemeral=True)

# /say コマンド：Botが代わりに話す
@bot.tree.command(name="say", description="Botが指定メッセージを代わりに話します")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

# /time コマンド：現在の時刻を東京タイムゾーンで表示
@bot.tree.command(name="time", description="現在の時刻（東京/JST）を表示します")
async def show_time(interaction: discord.Interaction):
    tokyo_tz = pytz.timezone("Asia/Tokyo")
    current_time = datetime.now(tokyo_tz).strftime("%Y-%m-%d %H:%M:%S JST")
    await interaction.response.send_message(f"現在の時刻（東京/JST）: {current_time}")
    
#/chatコマンド:Geminiとチャット
@bot.tree.command(name="chat", description="Geminiとチャットします")
async def chat(interaction: discord.Interaction, message: str):
    global conversation_history
    await interaction.response.defer()  # 処理中であることをユーザーに通知

    # チャット履歴にメッセージを追加
    conversation_history.append(message)

    try:
        # Gemini APIにメッセージを送信（非同期処理）
        response = await asyncio.to_thread(gemini_chat, message)

        # Gemini APIからのレスポンスを送信
        await interaction.followup.send(response)

    except Exception as e:
        # エラーメッセージをユーザーに送信
        await interaction.followup.send(f"エラーが発生しました: {str(e)}")

# /chat_clear コマンド：チャット履歴を削除
@bot.tree.command(name="chat_clear", description="チャット履歴を削除します")
async def clear_chat(interaction: discord.Interaction):
    global conversation_history
    conversation_history.clear()  # 会話履歴をクリア
    await interaction.response.send_message("チャット履歴を削除しました。")
@bot.tree.command(
    name="random",
    description="ランダムにあなたの名前を変更します"
)
async def random_name(interaction: discord.Interaction):
    random_names = [
        "受験面倒くさいンゴ…", 
        "やべぇなw", 
        "我はねんねこ信者", 
        "鯖主つおい", 
        "ねんねこには勝てん", 
        "誰か助けてクレメンスw",
        "やばい…いつになったら約束の地に行けるんだ…",
        "鯖主は東方projectの博麗霊夢が推しですw",
        "反ねんねこは滅ぶべし"
        
    ]
    new_name = random.choice(random_names)  # ランダムで名前を選ぶ
    try:
        # 実行したユーザーのニックネームを変更
        await interaction.user.edit(nick=new_name)
        await interaction.response.send_message(f"あなたの新しい名前は「{new_name}」です!")
    except discord.Forbidden:
        await interaction.response.send_message("名前を変更できませんでした。Botに権限があるか確認してください。")
    except discord.HTTPException:
        await interaction.response.send_message("名前を変更する際にエラーが発生しました。")

# Wikipedia APIを使用した検索コマンド
@bot.tree.command(name="wiki", description="Wikipediaから情報を取得します")
async def wiki(interaction: discord.Interaction, query: str):
    await interaction.response.defer()  # 処理中メッセージを表示
    try:
        wikipedia.set_lang("ja")  # Wikipediaの言語を日本語に設定
        summary = wikipedia.summary(query, sentences=2)  # 要約を取得
        page_url = wikipedia.page(query).url  # ページURLを取得
        embed = discord.Embed(
            title=f"Wikipedia: {query}",
            description=summary,
            color=discord.Colour.green()
        ).add_field(name="詳細リンク", value=f"[こちら]({page_url})")
        await interaction.followup.send(embed=embed)
    except wikipedia.exceptions.DisambiguationError as e:
        await interaction.followup.send(f"曖昧なキーワードです。次の候補から選択してください: {', '.join(e.options[:5])}...")
    except wikipedia.exceptions.PageError:
        await interaction.followup.send("指定されたキーワードのページが見つかりませんでした。")
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {str(e)}")

# サーバー情報を表示するコマンド
@bot.tree.command(name="server", description="サーバーの情報を表示します")
async def server_info(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"サーバー情報: {guild.name}",
        color=discord.Colour.blue()
    )
    embed.add_field(name="サーバー名", value=guild.name, inline=False)
    embed.add_field(name="サーバーID", value=guild.id, inline=False)
    embed.add_field(name="メンバー数", value=guild.member_count, inline=False)
    embed.add_field(name="オーナー", value=str(guild.owner), inline=False)
    embed.add_field(name="サーバー作成日", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed)

# アキネーターゲームを開始するコマンドを追加
@bot.tree.command(name="akinator", description="アキネーターと遊びます")
async def akinator(interaction: discord.Interaction):
    await interaction.response.send_message("アキネーターを開始します。質問に答えてください！")
    
    # Akinatorのインスタンスを作成してゲームを開始
    akinator = Akinator()
    akinator.start_game()
    
    # ゲームの進行
    while True:
        try:
            # 質問を表示
            question = akinator.question
            await interaction.followup.send(question)
            
            # ユーザーからの入力を待機
            response = await bot.wait_for('message', check=lambda m: m.author == interaction.user)
            answer = response.content.lower()
            
            # 「戻る」機能
            if answer == 'b':
                akinator.go_back()
            else:
                # 回答をアキネーターに送信
                akinator.post_answer(answer)
                
                # 正解が出た場合
                if akinator.answer_id:
                    result = f"{akinator.name} / {akinator.description}"
                    await interaction.followup.send(f"アキネーターの答えは: {result}")
                    
                    # 正解かどうか確認
                    await interaction.followup.send("これは正しいですか？ (y/n)")
                    confirmation = await bot.wait_for('message', check=lambda m: m.author == interaction.user)
                    if confirmation.content.lower() == 'y':
                        await interaction.followup.send("ゲーム終了！ありがとうございました！")
                        break
                    elif confirmation.content.lower() == 'n':
                        akinator.exclude()
                else:
                    await interaction.followup.send("答えが分かりませんでした。再試行します。")
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {e}")
            break
            
# Botを実行
keep_alive()
bot.run(TOKEN)
