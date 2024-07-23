import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Botの準備
bot = commands.Bot(command_prefix='!', intents=intents)

# Botが起動したときのイベント
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# スラッシュコマンドの定義
@bot.tree.command(name="color", description="指定した色の名前でロールを作成し、自分に付与します。")
@app_commands.describe(color="ロールの色（16進数）")
async def color(interaction: discord.Interaction, color: str):
    guild = interaction.guild
    member = interaction.user

    try:
        # カラーコードを16進数から整数に変換
        color_value = int(color, 16)
        color_obj = discord.Color(color_value)

        # 既存の同名のロールがあるか確認
        role = discord.utils.get(guild.roles, name=f'#{color}')

        if not role:
            # 同名のロールがない場合は作成
            role = await guild.create_role(name=f'#{color}', color=color_obj)

            # ボットの最上位ロールの位置を取得
            bot_member = guild.get_member(bot.user.id)
            if bot_member:
                bot_top_role = bot_member.top_role
                bot_top_role_position = bot_top_role.position
            else:
                bot_top_role_position = None  # デフォルトの位置

            # 新しいロールの位置をボットのロールの1つ下に設定
            if bot_top_role_position is not None:
                new_position = bot_top_role_position - 1
                if new_position >= 0:
                    await role.edit(position=new_position)

        # 作成したロールをユーザーに付与
        await member.add_roles(role)

        # メッセージでロールとユーザーのIDを表示
        role_mention = f'<@&{role.id}>'
        user_mention = f'<@{member.id}>'
        await interaction.response.send_message(f'ロール {role_mention} が {user_mention} に付与されました。', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'ロールの作成または付与に失敗しました: {e}', ephemeral=True)

# 環境変数からトークンを取得してBotを起動
bot.run(os.getenv("DISCORD_TOKEN"))
