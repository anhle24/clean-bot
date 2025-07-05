import discord
from discord import app_commands
from discord.ui import View, Button
from flask import Flask
from threading import Thread
import os

# --- Flask app to keep bot alive ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Discord Bot Setup ---
TOKEN = os.getenv('DISCORD_TOKEN')  # Đảm bảo set biến môi trường trên Render

GUILD_ID = 1388137676900663347  # ✅ GUILD ID đã điền để sync lệnh slash ngay

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- Slash Command: /clear_all ---
@tree.command(name="clear_all", description="Xoá toàn bộ tin nhắn trong kênh hiện tại")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_all(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Lệnh này chỉ hoạt động trong server.", ephemeral=True)
        return

    class ConfirmView(View):
        def __init__(self):
            super().__init__(timeout=15)
            self.value = None

        @discord.ui.button(label="✅ Xác nhận xoá", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction_button: discord.Interaction, button: Button):
            self.value = True
            await interaction_button.response.edit_message(content="⏳ Đang xoá tin nhắn...", view=None)
            self.stop()

        @discord.ui.button(label="❌ Huỷ", style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction_button: discord.Interaction, button: Button):
            self.value = False
            await interaction_button.response.edit_message(content="❌ Đã huỷ xoá tin nhắn.", view=None)
            self.stop()

    view = ConfirmView()
    await interaction.response.send_message(
        "⚠️ Bạn có chắc muốn xoá **toàn bộ tin nhắn** trong kênh này không?",
        view=view,
        ephemeral=True
    )
    await view.wait()

    if view.value:
        try:
            deleted = await interaction.channel.purge(limit=1000)
            await interaction.followup.send(f"✅ Đã xoá **{len(deleted)}** tin nhắn trong <#{interaction.channel.id}>.", ephemeral=False)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi khi xoá tin nhắn: `{e}`", ephemeral=True)
    elif view.value is None:
        await interaction.followup.send("⌛ Hết thời gian xác nhận. Lệnh đã bị huỷ.", ephemeral=True)

# --- On Bot Ready ---
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Slash command đã được sync cho server {GUILD_ID} với tên {client.user}")

# --- Run bot ---
keep_alive()
client.run(TOKEN)
