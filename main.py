import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_TOKEN")

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
        # 不要な色ロールを削除
        await remove_empty_color_roles(after.guild)

# 誰も居ない色ロールを削除
async def remove_empty_color_roles(guild: discord.Guild):
    for role in guild.roles:
        if role.name.startswith('#') and len(role.members) == 0:
            try:
                await role.delete(reason="Unused color role cleanup")
                print(f'Deleted unused color role: {role.name}')
            except discord.HTTPException as e:
                print(f'Failed to delete role {role.name}: {e}')
            await asyncio.sleep(1)  # Add a delay to prevent hitting rate limits

# スラッシュコマンドの定義

class ColorGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="color", description="色ロールを変更または削除します。")

    @app_commands.command(name="change", description="指定した色のロールを自分に付与します。")
    @app_commands.describe(color="ロールの色（HEX）")
    async def change(self, interaction: discord.Interaction, color: str):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user

        try:
            if color is None or not color.strip():
                await interaction.followup.send('カラーコードが必要です。', ephemeral=True)
                return

            color = color.lstrip('#')
            color_value = int(color, 16)
            color_obj = discord.Color(color_value)

            role = discord.utils.get(guild.roles, name=f'#{color}')

            if not role:
                role = await guild.create_role(name=f'#{color}', color=color_obj)

                bot_member = guild.get_member(bot.user.id)
                if bot_member:
                    bot_top_role = bot_member.top_role
                    bot_top_role_position = bot_top_role.position
                else:
                    bot_top_role_position = None

                if bot_top_role_position is not None:
                    roles = guild.roles
                    role_positions = {role: role.position for role in roles}

                    role_positions[role] = bot_top_role_position - 1

                    sorted_roles = sorted(role_positions.items(), key=lambda x: x[1], reverse=True)
                    await guild.edit_role_positions(positions={r: p for r, p in sorted_roles})

            color_roles = [r for r in member.roles if r.name.startswith('#') and r != role]
            if color_roles:
                await member.remove_roles(*color_roles)

            await member.add_roles(role)

            role_mention = f'<@&{role.id}>'
            user_mention = f'<@{member.id}>'
            await interaction.followup.send(f'ロール {role_mention} が {user_mention} に付与されました。', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'ロールの作成または付与に失敗しました: {e}', ephemeral=True)

    @app_commands.command(name="remove", description="自分の色のロールを削除します。")
    async def remove(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user

        try:
            color_roles = [r for r in member.roles if r.name.startswith('#')]
            if color_roles:
                await member.remove_roles(*color_roles)
                await interaction.followup.send('現在の色ロールが削除されました。', ephemeral=True)
            else:
                await interaction.followup.send('削除する色ロールがありません。', ephemeral=True)

            await remove_empty_color_roles(guild)
        except Exception as e:
            await interaction.followup.send(f'ロールの削除に失敗しました: {e}', ephemeral=True)

# Botにサブコマンドグループを登録
bot.tree.add_command(ColorGroup())

@bot.tree.command(name="help", description="利用可能なコマンドの情報を表示します。")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ヘルプ - スラッシュコマンド",
        description="このBotで使用可能なスラッシュコマンドの一覧です。",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="/color change <HEX>",
        value=(
            "指定したHEXカラーのロールを自分に付与します。\n"
            "**HEX**: 色コードを指定します（例: `FF5733`）。"
        ),
        inline=False
    )

    embed.add_field(
        name="/color remove",
        value=(
            "自分の色ロールを削除します。"
        ),
        inline=False
    )

    embed.add_field(
        name="/HEX",
        value=(
            "HEXカラーの例を表示します。"
        ),
        inline=False
    )

    embed.set_footer(text="HEXコードは16進数の形式で指定してください。")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# /hexコマンドの定義
@bot.tree.command(name="hex", description="HEXカラーの例を表示します。")
async def hex_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="HEXカラーの例",
        description="以下はHEXカラーの例です。カラーコードは対応する色で表示されています。",
        color=discord.Color.blue()
    )

    # 各色の例を追加
    embed.add_field(
        name="赤",
        value="`#FF0000`",
        inline=False
    )

    embed.add_field(
        name="青",
        value="`#0000FF`",
        inline=False
    )

    embed.add_field(
        name="黄色",
        value="`#FFFF00`",
        inline=False
    )

    embed.add_field(
        name="シアン",
        value="`#00FFFF`",
        inline=False
    )

    embed.add_field(
        name="マゼンタ",
        value="`#FF00FF`",
        inline=False
    )

    embed.add_field(
        name="オレンジ",
        value="`#FFA500`",
        inline=False
    )

    embed.add_field(
        name="紫",
        value="`#800080`",
        inline=False
    )

    embed.add_field(
        name="ライム",
        value="`#00FF00`",
        inline=False
    )

    embed.add_field(
        name="ピンク",
        value="`#FFC0CB`",
        inline=False
    )

    embed.add_field(
        name="グレー",
        value="`#808080`",
        inline=False
    )

    embed.add_field(
        name="茶色",
        value="`#A52A2A`",
        inline=False
    )

    embed.add_field(
        name="ベージュ",
        value="`#F5F5DC`",
        inline=False
    )

    embed.add_field(
        name="ターコイズ",
        value="`#40E0D0`",
        inline=False
    )

    embed.add_field(
        name="オリーブ",
        value="`#808000`",
        inline=False
    )

    embed.add_field(
        name="コーラル",
        value="`#FF7F50`",
        inline=False
    )

    embed.add_field(
        name="スカイブルー",
        value="`#87CEEB`",
        inline=False
    )

    embed.add_field(
        name="インディゴ",
        value="`#4B0082`",
        inline=False
    )

    embed.add_field(
        name="サーモン",
        value="`#FA8072`",
        inline=False
    )

    embed.add_field(
        name="ライトグリーン",
        value="`#90EE90`",
        inline=False
    )

    embed.add_field(
        name="ダークオレンジ",
        value="`#FF8C00`",
        inline=False
    )

    embed.add_field(
        name="白",
        value="`#FFFFFF`",
        inline=False
    )

    embed.set_footer(text="カラーコードは16進数の形式です。")

    await interaction.response.send_message(embed=embed, ephemeral=True)


try:
    keep_alive()
    bot.run(TOKEN)
except Exception as e:
    print(f'エラーが発生しました: {e}')
