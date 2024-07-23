import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # メンバーの更新を監視するために必要

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

# メンバーの更新を監視
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # ロールが変更された場合にのみ処理を行う
    if before.roles != after.roles:
        guild = after.guild
        await remove_empty_color_roles(guild)

# 誰も居ない色ロールを削除
async def remove_empty_color_roles(guild: discord.Guild):
    for role in guild.roles:
        if role.name.startswith('#'):
            if len(role.members) == 0:
                try:
                    await role.delete(reason="Unused color role cleanup")
                    print(f'Deleted unused color role: {role.name}')
                except discord.HTTPException as e:
                    print(f'Failed to delete role {role.name}: {e}')
                await asyncio.sleep(1)  # Add a delay to prevent hitting rate limits

# スラッシュコマンドの定義
@bot.tree.command(name="color", description="指定した色の名前でロールを作成し、自分に付与します。")
@app_commands.describe(color="ロールの色（16進数）")
async def color(interaction: discord.Interaction, color: str):
    await interaction.response.defer(ephemeral=True)  # Defer the response

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

            # ボットのロールの位置を取得
            bot_member = guild.get_member(bot.user.id)
            if bot_member:
                bot_top_role = bot_member.top_role
                bot_top_role_position = bot_top_role.position
            else:
                bot_top_role_position = None

            # ロールをボットの1つ下に移動
            if bot_top_role_position is not None:
                # サーバー内のすべてのロールを取得
                roles = guild.roles
                role_positions = {role: role.position for role in roles}

                # 作成したロールの位置をボットのロールの1つ下に設定
                role_positions[role] = bot_top_role_position - 1

                # ロールの位置を更新
                sorted_roles = sorted(role_positions.items(), key=lambda x: x[1], reverse=True)
                await guild.edit_role_positions(positions={r: p for r, p in sorted_roles})

        # 既存の色ロールを削除
        color_roles = [r for r in member.roles if r.name.startswith('#') and r != role]
        if color_roles:
            await member.remove_roles(*color_roles)

        # 作成したロールをユーザーに付与
        await member.add_roles(role)

        # メッセージでロールとユーザーのIDを表示
        role_mention = f'<@&{role.id}>'
        user_mention = f'<@{member.id}>'
        await interaction.followup.send(f'ロール {role_mention} が {user_mention} に付与されました。', ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f'ロールの作成または付与に失敗しました: {e}', ephemeral=True)

# 環境変数からトークンを取得してBotを起動
bot.run(os.getenv("DISCORD_TOKEN"))
