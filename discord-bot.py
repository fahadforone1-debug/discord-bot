import discord
from discord.ext import commands
import datetime
import json
from dotenv import load_dotenv; load_dotenv()
import os
import time
import asyncio

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
DEFAULT_GIF_URL = "https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.pinterest.com%2Fpin%2Fsawunn-gif-sawunn-discover-share-gifs--304485624819377454%2F&psig=AOvVaw3GNjLXARRjb5VZRiFS4jK9&ust=1759527120078000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCIjx_bq7hpADFQAAAAAdAAAAABAE"

# نظام منع التكرار السريع (Rate Limiting)
last_command_time = {}

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

def check_rate_limit(user_id, command_name, cooldown_seconds=5):
    """
    التحقق من rate limiting لمنع التكرار السريع
    """
    current_time = time.time()
    key = f"{user_id}_{command_name}"
    
    if key in last_command_time:
        time_diff = current_time - last_command_time[key]
        if time_diff < cooldown_seconds:
            return False, int(cooldown_seconds - time_diff) + 1
    
    last_command_time[key] = current_time
    return True, 0

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is now online!")
    guild_count = len(bot.guilds)
    await bot.change_presence(activity=discord.Game(name=f"Welcome System | {guild_count} servers | !help_welcome"))

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
    # التحقق من rate limiting لمنع التكرار السريع
    can_use, wait_time = check_rate_limit(ctx.author.id, "setup_welcome", 10)
    if not can_use:
        embed = discord.Embed(
            title="⏰ يرجى الانتظار",
            description=f"يرجى الانتظار {wait_time} ثانية قبل استخدام هذا الأمر مرة أخرى",
            color=0xffaa00
        )
        await ctx.send(embed=embed, delete_after=5)
        return
    
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
    embed.add_field(
        name="⚠️ تنبيه:",
        value="إذا كان البوت يرسل رسائل مكررة، استخدم `!reload_settings` لإعادة التشغيل",
        inline=False
    )
    
    # إضافة معلومات المطور
    try:
        developer = bot.get_user(DEVELOPER_ID) or await bot.fetch_user(DEVELOPER_ID)
        embed.set_footer(
            text=f"💻 تم تطوير البوت بواسطة {developer.display_name}",
            icon_url=developer.display_avatar.url
        )
    except:
        embed.set_footer(
            text=f"💻 تم تطوير البوت بواسطة {DEVELOPER_NAME}",
            icon_url="https://cdn.discordapp.com/embed/avatars/0.png"
        )
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def welcome_gif(ctx, gif_url: str = None):
    """
    تغيير GIF الترحيب
    مثال: !welcome_gif https://media.giphy.com/media/xyz/giphy.gif
    أو !welcome_gif default لاستخدام الافتراضي
    """
    settings = get_welcome_settings(ctx.guild.id)
    if not settings:
        await ctx.send("❌ يجب إعداد نظام الترحيب أولاً باستخدام `!setup_welcome`")
        return
    
    # إذا لم يتم توفير رابط أو كان "default"
    if not gif_url or gif_url.lower() == "default":
        gif_url = DEFAULT_GIF_URL
        action_text = "تم تعيين GIF الافتراضي"
    else:
        action_text = "تم تغيير GIF الترحيب"
    
    # التحقق من صحة الرابط
    if not (gif_url.startswith('http://') or gif_url.startswith('https://')):
        await ctx.send("❌ يرجى إدخال رابط صحيح يبدأ بـ http:// أو https://")
        return
    
    # حفظ الإعدادات الجديدة
    save_welcome_settings(
        ctx.guild.id, 
        settings["channel_id"], 
        settings["message"], 
        settings.get("embed_color", 0x00bfff),
        gif_url
    )
    
    embed = discord.Embed(
        title=f"✅ {action_text}",
        description=f"**الرابط الجديد:** {gif_url}",
        color=0x00ff00
    )
    
    try:
        embed.set_image(url=gif_url)
    except:
        embed.add_field(name="⚠️ تحذير", value="قد يكون الرابط غير صالح للعرض", inline=False)
    
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
    # التحقق من rate limiting لمنع التكرار السريع
    can_use, wait_time = check_rate_limit(ctx.author.id, "test_welcome", 5)
    if not can_use:
        embed = discord.Embed(
            title="⏰ يرجى الانتظار",
            description=f"يرجى الانتظار {wait_time} ثانية قبل اختبار الترحيب مرة أخرى",
            color=0xffaa00
        )
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=3)
        return
    
    if not member:
        member = ctx.author
    
    settings = get_welcome_settings(ctx.guild.id)
    if not settings:
        await ctx.send("❌ يجب إعداد نظام الترحيب أولاً باستخدام `!setup_welcome`")
        return
    
    welcome_channel = ctx.guild.get_channel(settings["channel_id"])
    if not welcome_channel:
        await ctx.send("❌ قناة الترحيب غير موجودة")
        return
    
    # إنشاء embed الاختبار (نفس تصميم الترحيب الأصلي)
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
    
    # صورة السيرفر
    if member.guild.icon:
        embed.set_author(name=member.guild.name, icon_url=member.guild.icon.url)
    
    # Footer للاختبار
    current_time = datetime.datetime.now()
    try:
        developer = bot.get_user(DEVELOPER_ID) or await bot.fetch_user(DEVELOPER_ID)
        embed.set_footer(
            text=f"🧪 TEST MODE - Powered By {developer.display_name} • {current_time.strftime('%I:%M%p').lower()}", 
            icon_url=developer.display_avatar.url
        )
    except:
        embed.set_footer(
            text=f"🧪 TEST MODE - Powered By {DEVELOPER_NAME} • {current_time.strftime('%I:%M%p').lower()}", 
            icon_url="https://cdn.discordapp.com/embed/avatars/0.png"
        )
    
    try:
        await welcome_channel.send(embed=embed)
        await ctx.send(f"✅ تم إرسال رسالة ترحيب تجريبية لـ {member.mention} في {welcome_channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ خطأ في إرسال رسالة الاختبار: {e}")

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
            
        # إضافة معلومات المطور
        try:
            developer = bot.get_user(DEVELOPER_ID) or await bot.fetch_user(DEVELOPER_ID)
            embed.set_footer(
                text=f"💻 تم تطوير البوت بواسطة {developer.display_name}",
                icon_url=developer.display_avatar.url
            )
        except:
            embed.set_footer(
                text=f"💻 تم تطوير البوت بواسطة {DEVELOPER_NAME}",
                icon_url="https://cdn.discordapp.com/embed/avatars/0.png"
            )
    
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
async def bot_stats(ctx):
    """
    عرض إحصائيات البوت
    """
    embed = discord.Embed(
        title="📊 إحصائيات البوت",
        color=0x00bfff
    )
    
    # عدد السيرفرات
    guild_count = len(bot.guilds)
    embed.add_field(name="🏰 السيرفرات", value=f"{guild_count} سيرفر", inline=True)
    
    # عدد الأعضاء الإجمالي
    total_members = sum(guild.member_count for guild in bot.guilds)
    embed.add_field(name="👥 الأعضاء", value=f"{total_members:,} عضو", inline=True)
    
    # عدد السيرفرات المفعل بها نظام الترحيب
    if os.path.exists(WELCOME_SETTINGS_FILE):
        with open(WELCOME_SETTINGS_FILE, "r") as f:
            data = json.load(f)
        active_welcomes = len(data)
    else:
        active_welcomes = 0
    
    embed.add_field(name="✅ نظام الترحيب مفعل", value=f"{active_welcomes} سيرفر", inline=True)
    
    # قائمة السيرفرات (أول 10 فقط لتجنب الرسائل الطويلة)
    guild_list = []
    for i, guild in enumerate(bot.guilds[:10], 1):
        guild_list.append(f"{i}. **{guild.name}** ({guild.member_count:,} عضو)")
    
    if len(bot.guilds) > 10:
        guild_list.append(f"... و {len(bot.guilds) - 10} سيرفر آخر")
    
    embed.add_field(
        name="🏰 قائمة السيرفرات:",
        value="\n".join(guild_list) if guild_list else "لا توجد سيرفرات",
        inline=False
    )
    
    embed.set_footer(text=f"Powered by {DEVELOPER_NAME}")
    await ctx.send(embed=embed)

@bot.command()
async def developer(ctx):
    """
    عرض معلومات مطور البوت
    """
    try:
        developer = bot.get_user(DEVELOPER_ID) or await bot.fetch_user(DEVELOPER_ID)
        
        embed = discord.Embed(
            title="👨‍💻 معلومات المطور",
            color=0x7289da
        )
        
        embed.set_thumbnail(url=developer.display_avatar.url)
        embed.add_field(name="🔰 اسم المطور", value=developer.display_name, inline=True)
        embed.add_field(name="🏷️ اسم المستخدم", value=f"{developer.name}#{developer.discriminator}", inline=True)
        embed.add_field(name="🆔 معرف المطور", value=DEVELOPER_ID, inline=True)
        embed.add_field(name="📅 انضم لديسكورد", value=developer.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="🤖 اسم البوت", value=bot.user.name, inline=True)
        embed.add_field(name="🌟 نوع البوت", value="Welcome System Bot", inline=True)
        
        embed.add_field(
            name="📝 وصف البوت:",
            value="بوت ترحيب متقدم يدعم عدة سيرفرات مع إعدادات منفصلة لكل سيرفر",
            inline=False
        )
        
        embed.set_footer(
            text=f"شكراً لاستخدام البوت! • {datetime.datetime.now().strftime('%Y-%m-%d')}",
            icon_url=bot.user.display_avatar.url
        )
        
    except Exception as e:
        embed = discord.Embed(
            title="👨‍💻 معلومات المطور",
            color=0x7289da
        )
        embed.add_field(name="🔰 اسم المطور", value=DEVELOPER_NAME, inline=True)
        embed.add_field(name="🆔 معرف المطور", value=DEVELOPER_ID, inline=True)
        embed.add_field(name="🤖 اسم البوت", value=bot.user.name, inline=True)
        embed.add_field(
            name="📝 وصف البوت:",
            value="بوت ترحيب متقدم يدعم عدة سيرفرات مع إعدادات منفصلة لكل سيرفر",
            inline=False
        )
        embed.set_footer(text=f"Error loading developer info: {e}")
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def reload_settings(ctx):
    """
    إعادة تحميل إعدادات الترحيب (في حالة وجود مشاكل)
    """
    try:
        # قراءة الإعدادات من الملف
        settings = get_welcome_settings(ctx.guild.id)
        if not settings:
            await ctx.send("❌ لا توجد إعدادات ترحيب لإعادة تحميلها")
            return
            
        embed = discord.Embed(
            title="✅ تم إعادة تحميل الإعدادات",
            description="تم إعادة تحميل إعدادات الترحيب بنجاح",
            color=0x00ff00
        )
        
        # عرض الإعدادات المحدثة
        channel = ctx.guild.get_channel(settings["channel_id"])
        embed.add_field(name="📢 قناة الترحيب", value=channel.mention if channel else "قناة محذوفة", inline=False)
        embed.add_field(name="💬 رسالة الترحيب", value=settings["message"], inline=False)
        embed.add_field(name="🎥 GIF", value=settings.get("gif_url", DEFAULT_GIF_URL), inline=False)
        
        # إظهار الـ GIF المحدث
        gif_url = settings.get("gif_url", DEFAULT_GIF_URL)
        if gif_url:
            embed.set_image(url=gif_url)
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ خطأ في إعادة تحميل الإعدادات: {e}")

@bot.command()
@commands.has_permissions(administrator=True)  
async def clear_duplicates(ctx, limit: int = 50):
    """
    مسح الرسائل المكررة من البوت في القناة الحالية
    مثال: !clear_duplicates 20
    """
    try:
        deleted = 0
        bot_messages = []
        
        # جلب آخر الرسائل في القناة
        async for message in ctx.channel.history(limit=limit):
            if message.author == bot.user:
                bot_messages.append(message)
        
        # البحث عن الرسائل المكررة
        seen_contents = set()
        to_delete = []
        
        for message in bot_messages:
            if message.embeds:
                embed_title = message.embeds[0].title if message.embeds[0].title else ""
                embed_desc = message.embeds[0].description if message.embeds[0].description else ""
                content_key = f"{embed_title}|{embed_desc}"
                
                if content_key in seen_contents and content_key.strip():
                    to_delete.append(message)
                else:
                    seen_contents.add(content_key)
        
        # حذف الرسائل المكررة
        for message in to_delete:
            try:
                await message.delete()
                deleted += 1
                await asyncio.sleep(0.5)  # تجنب rate limit
            except:
                pass
        
        if deleted > 0:
            embed = discord.Embed(
                title="🧹 تم مسح الرسائل المكررة",
                description=f"تم حذف {deleted} رسالة مكررة",
                color=0x00ff00
            )
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=5)  # حذف الرسالة بعد 5 ثوان
        else:
            embed = discord.Embed(
                title="✅ لا توجد رسائل مكررة",
                description="لم يتم العثور على رسائل مكررة لحذفها",
                color=0x00bfff
            )
            msg = await ctx.send(embed=embed)
            await msg.delete(delay=3)
            
    except Exception as e:
        await ctx.send(f"❌ خطأ في مسح الرسائل: {e}")

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
        ("!reload_settings", "إعادة تحميل الإعدادات"),
        ("!clear_duplicates [عدد]", "مسح الرسائل المكررة"),
        ("!bot_stats", "عرض إحصائيات البوت"),
        ("!developer", "عرض معلومات مطور البوت"),
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
    
    # إضافة معلومات المطور
    try:
        developer = bot.get_user(DEVELOPER_ID) or await bot.fetch_user(DEVELOPER_ID)
        embed.set_footer(
            text=f"💻 تم تطوير البوت بواسطة {developer.display_name} ({DEVELOPER_NAME})",
            icon_url=developer.display_avatar.url
        )
    except:
        embed.set_footer(
            text=f"💻 تم تطوير البوت بواسطة {DEVELOPER_NAME}",
            icon_url="https://cdn.discordapp.com/embed/avatars/0.png"
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

# اقرأ المتغير من ملف .env أو متغيرات البيئة
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ Environment variable DISCORD_TOKEN is missing")
    raise SystemExit(1)

bot.run(TOKEN)
