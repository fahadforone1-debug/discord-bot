import discord
from discord.ext import commands
import datetime
import json
from dotenv import load_dotenv; load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ملف حفظ إعدادات السيرفرات
WELCOME_SETTINGS_FILE = "welcome_settings.json"

# معلومات المطور (ضع معرف حسابك هنا)
DEVELOPER_NAME = "Dev fahad"  # ضع اسمك هنا
DEVELOPER_ID = 941670030494531584  # ضع معرف حسابك في ديسكورد هنا

# رابط GIF افتراضي
DEFAULT_GIF_URL = "https://media.discordapp.net/attachments/1264550914056786002/1408009869537054810/bannner.gif?ex=68df8de0&is=68de3c60&hm=81d203da5070347b954bd9f247529dc2b003729cd540d023d33e657dc0a8c4fd&=&width=940&height=528"

def save_welcome_settings(guild_id, channel_id, message, embed_color=0x00bfff, gif_url=None):
    if os.path.exists(WELCOME_SETTINGS_FILE):
        with open(WELCOME_SETTINGS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data[str(guild_id)] = {
        "channel_id": channel_id,
        "message": message,
        "embed_color": embed_color,
        "gif_url": gif_url or DEFAULT_GIF_URL
    }
    with open(WELCOME_SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_welcome_settings(guild_id):
    if os.path.exists(WELCOME_SETTINGS_FILE):
        with open(WELCOME_SETTINGS_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(guild_id))
    return None

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is now online!")
    await bot.change_presence(activity=discord.Game(name="Welcome System | !help"))

@bot.event
async def on_member_join(member):
    settings = get_welcome_settings(member.guild.id)
    # إذا لم يتم إعداد نظام الترحيب، لا يرسل البوت أي شيء
    if not settings:
        print(f"❌ نظام الترحيب غير مفعل في سيرفر: {member.guild.name}")
        return
    
    welcome_channel = member.guild.get_channel(settings["channel_id"])
    # إذا لم يجد القناة المحددة، لا يرسل البوت أي شيء
    if not welcome_channel:
        print(f"❌ قناة الترحيب غير موجودة في سيرفر: {member.guild.name}")
        return
    
    # إنشاء الإيمبد بدون timestamp لحل مشكلة التوقيت المزدوج
    embed = discord.Embed(
        title=f"🎉 Welcome to {member.guild.name}!",
        description=settings["message"].replace("{user}", member.mention).replace("{guild}", member.guild.name).replace("{count}", str(member.guild.member_count)),
        color=settings.get("embed_color", 0x00bfff)
    )
    
    # معلومات العضو
    embed.add_field(name="👤 Username", value=f"{member.name}#{member.discriminator}", inline=True)
    embed.add_field(name="🆔 User ID", value=member.id, inline=True)
    embed.add_field(name="📅 Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    
    # معلومات السيرفر
    embed.add_field(name="👥 Member Count", value=member.guild.member_count, inline=True)
    embed.add_field(name="🏆 You're Member", value=f"#{member.guild.member_count}", inline=True)
    embed.add_field(name="🌟 Join Method", value="Direct Join", inline=True)
    
    # صورة العضو
    embed.set_thumbnail(url=member.display_avatar.url)
    
    # إضافة GIF
    gif_url = settings.get("gif_url", DEFAULT_GIF_URL)
    if gif_url:
        embed.set_image(url=gif_url)
    
    # صورة السيرفر (إذا كان لديه صورة)
    if member.guild.icon:
        embed.set_author(name=member.guild.name, icon_url=member.guild.icon.url)
    
    # Footer مع معلومات المطور - استخدام التوقيت المحلي الصحيح
    current_time = datetime.datetime.now()  # التوقيت المحلي بدلاً من UTC
    try:
        developer = bot.get_user(DEVELOPER_ID) or await bot.fetch_user(DEVELOPER_ID)
        embed.set_footer(
            text=f"Powered By {developer.display_name} • Today at {current_time.strftime('%I:%M%p').lower()}", 
            icon_url=developer.display_avatar.url
        )
    except:
        # في حالة فشل جلب المعلومات
        embed.set_footer(
            text=f"Powered By {DEVELOPER_NAME} • Today at {current_time.strftime('%I:%M%p').lower()}", 
            icon_url="https://cdn.discordapp.com/embed/avatars/0.png"
        )
    
    try:
        # البوت يرسل فقط في القناة المحددة
        await welcome_channel.send(embed=embed)
        print(f"✅ تم إرسال رسالة ترحيب لـ {member.name} في قناة {welcome_channel.name}")
    except Exception as e:
        print(f"❌ خطأ في إرسال رسالة الترحيب: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_welcome(ctx, channel: discord.TextChannel, *, message: str):
    """
    إعداد نظام الترحيب
    مثال: !setup_welcome #welcome مرحباً {user} في {guild}! أنت العضو رقم {count}
    """
    save_welcome_settings(ctx.guild.id, channel.id, message)
    
    embed = discord.Embed(
        title="✅ تم إعداد نظام الترحيب",
        description=f"**القناة:** {channel.mention}\n**الرسالة:** {message}",
        color=0x00ff00
    )
    embed.add_field(
        name="📢 ملاحظة مهمة:",
        value=f"البوت سيرسل رسائل الترحيب **فقط** في قناة {channel.mention}\nولن يرسل في أي قناة أخرى.",
        inline=False
    )
    embed.add_field(
        name="المتغيرات المتاحة:",
        value="`{user}` - منشن العضو\n`{guild}` - اسم السيرفر\n`{count}` - عدد الأعضاء",
        inline=False
    )
    embed.add_field(
        name="🎥 GIF:",
        value=f"تم تعيين GIF افتراضي. يمكنك تغييره بأمر `!welcome_gif <رابط>`",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def welcome_gif(ctx, gif_url: str):
    """
    تغيير GIF الترحيب
    مثال: !welcome_gif https://media.giphy.com/media/xyz/giphy.gif
    """
    settings = get_welcome_settings(ctx.guild.id)
    if not settings:
        await ctx.send("❌ يجب إعداد نظام الترحيب أولاً باستخدام `!setup_welcome`")
        return
    
    save_welcome_settings(
        ctx.guild.id, 
        settings["channel_id"], 
        settings["message"], 
        settings.get("embed_color", 0x00bfff),
        gif_url
    )
    
    embed = discord.Embed(
        title="✅ تم تغيير GIF الترحيب",
        color=0x00ff00
    )
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def welcome_color(ctx, color: str):
    """
    تغيير لون الإيمبد
    مثال: !welcome_color #ff0000 أو !welcome_color red
    """
    settings = get_welcome_settings(ctx.guild.id)
    if not settings:
        await ctx.send("❌ يجب إعداد نظام الترحيب أولاً باستخدام `!setup_welcome`")
        return
    
    # تحويل اللون
    try:
        if color.startswith('#'):
            embed_color = int(color[1:], 16)
        else:
            color_map = {
                'red': 0xff0000, 'green': 0x00ff00, 'blue': 0x0000ff,
                'yellow': 0xffff00, 'purple': 0x800080, 'orange': 0xffa500,
                'pink': 0xffc0cb, 'cyan': 0x00ffff, 'magenta': 0xff00ff
            }
            embed_color = color_map.get(color.lower(), 0x00bfff)
        
        save_welcome_settings(
            ctx.guild.id, 
            settings["channel_id"], 
            settings["message"], 
            embed_color,
            settings.get("gif_url")
        )
        
        embed = discord.Embed(
            title="✅ تم تغيير لون الترحيب",
            color=embed_color
        )
        await ctx.send(embed=embed)
        
    except ValueError:
        await ctx.send("❌ لون غير صالح. استخدم كود hex مثل #ff0000 أو اسم لون مثل red")

@bot.command()
@commands.has_permissions(administrator=True)
async def change_welcome_channel(ctx, new_channel: discord.TextChannel):
    """
    تغيير قناة الترحيب
    مثال: !change_welcome_channel #new-welcome
    """
    settings = get_welcome_settings(ctx.guild.id)
    if not settings:
        await ctx.send("❌ يجب إعداد نظام الترحيب أولاً باستخدام `!setup_welcome`")
        return
    
    save_welcome_settings(
        ctx.guild.id, 
        new_channel.id, 
        settings["message"], 
        settings.get("embed_color", 0x00bfff),
        settings.get("gif_url")
    )
    
    embed = discord.Embed(
        title="✅ تم تغيير قناة الترحيب",
        description=f"القناة الجديدة: {new_channel.mention}",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def test_welcome(ctx, member: discord.Member = None):
    """
    اختبار رسالة الترحيب
    مثال: !test_welcome @عضو
    """
    if not member:
        member = ctx.author
    
    settings = get_welcome_settings(ctx.guild.id)
    if not settings:
        await ctx.send("❌ يجب إعداد نظام الترحيب أولاً باستخدام `!setup_welcome`")
        return
    
    # محاكاة حدث انضمام عضو
    await on_member_join(member)
    await ctx.send(f"✅ تم إرسال رسالة ترحيب تجريبية لـ {member.mention}")

@bot.command()
async def welcome_info(ctx):
    """
    عرض إعدادات الترحيب الحالية
    """
    settings = get_welcome_settings(ctx.guild.id)
    if not settings:
        embed = discord.Embed(
            title="❌ نظام الترحيب غير مفعل",
            description="استخدم `!setup_welcome` لتفعيل نظام الترحيب",
            color=0xff0000
        )
    else:
        channel = ctx.guild.get_channel(settings["channel_id"])
        embed = discord.Embed(
            title="📋 إعدادات نظام الترحيب",
            color=settings.get("embed_color", 0x00bfff)
        )
        embed.add_field(name="📢 قناة الترحيب", value=channel.mention if channel else "قناة محذوفة", inline=False)
        embed.add_field(name="💬 رسالة الترحيب", value=settings["message"], inline=False)
        embed.add_field(name="🎨 لون الإيمبد", value=f"#{settings.get('embed_color', 0x00bfff):06x}", inline=False)
        embed.add_field(name="🎥 GIF", value=settings.get("gif_url", "لا يوجد"), inline=False)
        embed.add_field(name="⚠️ ملاحظة", value="البوت يرسل **فقط** في القناة المحددة أعلاه", inline=False)
        
        # إظهار GIF الحالي
        gif_url = settings.get("gif_url")
        if gif_url:
            embed.set_image(url=gif_url)
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def disable_welcome(ctx):
    """
    تعطيل نظام الترحيب
    """
    if os.path.exists(WELCOME_SETTINGS_FILE):
        with open(WELCOME_SETTINGS_FILE, "r") as f:
            data = json.load(f)
        if str(ctx.guild.id) in data:
            del data[str(ctx.guild.id)]
            with open(WELCOME_SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=4)
            
            embed = discord.Embed(
                title="✅ تم تعطيل نظام الترحيب",
                description="البوت لن يرسل أي رسائل ترحيب بعد الآن",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ نظام الترحيب غير مفعل أصلاً")
    else:
        await ctx.send("❌ نظام الترحيب غير مفعل أصلاً")

@bot.command()
async def help_welcome(ctx):
    """
    عرض مساعدة أوامر نظام الترحيب
    """
    embed = discord.Embed(
        title="📚 أوامر نظام الترحيب",
        description="جميع أوامر نظام الترحيب المتاحة",
        color=0x00bfff
    )
    
    commands_list = [
        ("!setup_welcome <#قناة> <رسالة>", "إعداد نظام الترحيب"),
        ("!welcome_gif <رابط>", "تغيير GIF الترحيب"),
        ("!change_welcome_channel <#قناة>", "تغيير قناة الترحيب"),
        ("!welcome_color <لون>", "تغيير لون الإيمبد"),
        ("!test_welcome [@عضو]", "اختبار رسالة الترحيب"),
        ("!welcome_info", "عرض الإعدادات الحالية"),
        ("!disable_welcome", "تعطيل نظام الترحيب"),
        ("!help_welcome", "عرض هذه المساعدة")
    ]
    
    for command, description in commands_list:
        embed.add_field(name=command, value=description, inline=False)
    
    embed.add_field(
        name="المتغيرات في رسالة الترحيب:",
        value="`{user}` - منشن العضو\n`{guild}` - اسم السيرفر\n`{count}` - عدد الأعضاء",
        inline=False
    )
    
    embed.add_field(
        name="⚠️ ملاحظة مهمة:",
        value="البوت يرسل رسائل الترحيب **فقط** في القناة المحددة عبر أمر `!setup_welcome`",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ ليس لديك صلاحية",
            description="تحتاج صلاحية Administrator لاستخدام هذا الأمر",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ ناقص معطى مطلوب. استخدم `!help_welcome` للمساعدة")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ معطى خاطئ. استخدم `!help_welcome` للمساعدة")

# ⚠️ ضع التوكن الجديد هنا
TOKEN = os.getenv("TOKEN")