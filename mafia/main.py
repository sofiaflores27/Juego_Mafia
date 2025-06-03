import discord
from discord.ext import commands
import os
import random

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

jugadores = []
roles = {}
mafiosos = []
victima = None
jugadores_necesarios = 0
partida_en_progreso = False
fase_noche = False
canal_mafia = None

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")

@bot.command()
async def crear(ctx, numero: int):
    global partida_en_progreso, jugadores, jugadores_necesarios
    if partida_en_progreso:
        await ctx.send("Ya hay una partida en curso.")
        return
    if numero < 4:
        await ctx.send("Se necesitan al menos 4 jugadores.")
        return
    jugadores.clear()
    jugadores.append(ctx.author)
    jugadores_necesarios = numero
    partida_en_progreso = True
    await ctx.send(f"{ctx.author.name} creó una partida para {numero} jugadores. Usa `!unirme` para entrar.")

@bot.command()
async def unirme(ctx):
    global partida_en_progreso, jugadores
    if not partida_en_progreso:
        await ctx.send("No hay partida activa.")
        return
    if ctx.author in jugadores:
        await ctx.send("Ya estás en la partida.")
        return
    jugadores.append(ctx.author)
    await ctx.send(f"{ctx.author.name} se unió. ({len(jugadores)}/{jugadores_necesarios})")

    if len(jugadores) == jugadores_necesarios:
        await iniciar_partida(ctx)

async def iniciar_partida(ctx):
    global roles, mafiosos, fase_noche, canal_mafia
    roles = asignar_roles(jugadores)
    mafiosos = [jugador for jugador, rol in roles.items() if rol == "Mafia"]

    # Crear un canal privado para los mafiosos
    guild = ctx.guild
    canal_mafia = await guild.create_text_channel('mafia-secreta')

    # Configurar permisos para el canal
    await canal_mafia.set_permissions(guild.default_role, read_messages=False)
    for mafioso in mafiosos:
        await canal_mafia.set_permissions(mafioso, read_messages=True, send_messages=True)

    for jugador, rol in roles.items():
        try:
            await jugador.send(f"🤫 Tu rol es: **{rol}**.")
        except Exception as e:
            await ctx.send(f"⚠️ No pude enviar mensaje a {jugador.name}.")

    fase_noche = True
    await ctx.send("🌙 ¡La fase de noche ha comenzado! Los mafiosos, elijan a su víctima.")

    # Notificar a los mafiosos en su canal privado
    await canal_mafia.send("🌙 Es la fase de noche. Usa `!matar <@jugador>` para elegir a quién eliminar.")

def asignar_roles(jugadores):
    # Asegúrate de que haya al menos un mafioso, un detective y un doctor si hay suficientes jugadores
    roles_list = ["Mafia", "Detective", "Doctor"] + ["Ciudadano"] * (len(jugadores) - 3)
    random.shuffle(roles_list)
    return {jugador: rol for jugador, rol in zip(jugadores, roles_list)}

@bot.command()
async def matar(ctx, jugador: discord.Member):
    global fase_noche, victima
    if ctx.channel != canal_mafia:
        await ctx.send("Este comando solo puede ser usado en el canal de la mafia.")
        return
    if not fase_noche:
        await ctx.send("Ahora no es la fase de noche.")
        return
    if ctx.author not in mafiosos:
        await ctx.send("Solo los mafiosos pueden usar este comando.")
        return
    if jugador not in jugadores:
        await ctx.send("Este jugador no está en la partida.")
        return

    victima = jugador
    await canal_mafia.send(f"Los mafiosos han elegido a {jugador.name} para eliminar. Se procesará al amanecer.")
    fase_noche = False

bot.run(TOKEN)
