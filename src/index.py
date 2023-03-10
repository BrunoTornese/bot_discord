import discord
import pytube
import os
import asyncio
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv


#cagado del token del bot
load_dotenv()
TOKEN = os.getenv('discord_token')

#declaracion de variables
client = discord.Client
intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
lista_canciones = []
cola_reproduccion = asyncio.Queue()  


#funcion para sumar
@bot.command(name= 'suma')
async def suma(ctx, n1, n2):
    suma = int(n1) + int(n2)
    await ctx.send(suma)

#funcion para multiplicar
@bot.command(name= 'multiplicar')
async def multiplicar(ctx, n1, n2):
    multiplicacion = int(n1) * int(n2)
    await ctx.send(multiplicacion)


#funcion para restar
@bot.command(name= 'restar')
async def restar(ctx, n1, n2):
    suma = int(n1) - int(n2)
    await ctx.send(suma)

#funcion para dividir
@bot.command(name= 'dividir')
async def dividir(ctx, n1, n2):
    suma = int(n1) // int(n2)
    await ctx.send(suma)

#funcion del bot cuando se incia muestra el mensaje de los comandos
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name = 'Con ! usas los comandos'))
    print('El Bot Esta Listo')


@bot.command(pass_context=True)
async def conectar(ctx):
    canal = ctx.author.voice # obtiene el canal de voz
    if not canal: # si no hay canal de voz
        await ctx.send('Debes estar en un canal de voz') # envia el mensaje de error
        return
    else:
        voice_client = get(bot.voice_clients, guild=ctx.guild) #verifica que el bot este en el canal de voz
        if voice_client and voice_client.is_connected(): # si el bot esta en el canal de voz
            await voice_client.move_to(canal) # mueve el bot al canal de voz
        else: # si el bot no esta en el canal de voz
            voice_client = await canal.connect() # conecta el bot al canal de voz



@bot.command()
async def play(ctx, url):
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("No est??s conectado a un canal de voz.")
        return

    # Agregar la canci??n a la lista de canciones o cola de reproducci??n
    video = pytube.YouTube(url) # busca el video a partir de la url
    audio = video.streams.filter(only_audio=True).first() # filtra el audio
    audio_file = audio.download() # descarga el audio
    if ctx.voice_client and ctx.voice_client.is_playing(): # si el bot esta reproduciendo
        await ctx.send("Canci??n agregada a la cola de reproducci??n.") # se envia un mensaje de que la cancion se agrego a la cola de reproducci??n
        await cola_reproduccion.put(audio_file) # agrega la canci??n a la cola de reproducci??n
    else: # si el bot no esta reproduciendo
        await ctx.send("Canci??n en reproducci??n.") # se envia un mensaje de que la cancion esta en reproducci??n
        lista_canciones.append(audio_file) # agrega la canci??n a la lista de canciones

        # Reproducir el archivo de audio si no se est?? reproduciendo nada
        if not ctx.voice_client and lista_canciones: # si el bot no esta reproduciendo nada
            voice_client = await voice_channel.connect() # conecta el bot al canal de voz
            source = discord.FFmpegPCMAudio(lista_canciones[0]) # carga el audio
            player = voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(cancion_terminada(e, ctx), bot.loop)) # reproducir el audio

            # Esperar hasta que el audio termine de reproducirse
            while voice_client.is_playing(): 
                await asyncio.sleep(1)

            # Esperar la duraci??n del video original de YouTube si est?? disponible
            if hasattr(audio, 'duration'):
                await asyncio.sleep(audio.duration)

            # Eliminar el archivo de audio
            if os.path.exists(audio_file):
                os.remove(audio_file)

            if lista_canciones: # verifica que haya canciones en la lista
                lista_canciones.pop(0) #elimina  el primer archivo de la lista

            # Reproducir la siguiente canci??n en la lista
            if lista_canciones: # verifica si hay canciones en la lista de canciones
                source = discord.FFmpegPCMAudio(lista_canciones[0]) # crea un objeto de audio del archivo de la primera canci??n en la lista
                player = ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(cancion_terminada(e, ctx), bot.loop)) #reproduce la canci??n usando el audio creado anteriormente y establece la funci??n "cancion_terminada" para que se ejecute cuando la canci??n termine de reproducirse.
            elif not lista_canciones and not cola_reproduccion.empty(): # verifica si no hay canciones en la lista de canciones y si la cola de reproducci??n no est?? vac??a
                cancion = await cola_reproduccion.get()# obtiene la primera canci??n de la cola de reproducci??n
                lista_canciones.append(cancion)# agrega la canci??n a la lista de canciones
                source = discord.FFmpegPCMAudio(lista_canciones[0]) # crea un objeto de audio 
                player = ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(cancion_terminada(e, ctx), bot.loop)) # y lo reproduce
            else: # si no hay canciones en la lista de canciones y la cola de reproduc
                await ctx.voice_client.disconnect() # desconecta el bot

async def cancion_terminada(error, ctx): 
    if error:
        print(f"Error en la canci??n: {error}")

    # Eliminar la canci??n de la lista de canciones
    if lista_canciones: # si la lista de canciones est?? vac??a
        lista_canciones.pop(0) # elimina la primera canci??n de la lista

    # Reproducir la siguiente canci??n en la lista
    if lista_canciones: # si la lista de canciones no est?? vac??a
        source = discord.FFmpegPCMAudio(lista_canciones[0]) # obtiene el archivo de audio
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(cancion_terminada(e, ctx), bot.loop)) # reproducir la canci??n


@bot.command()
async def stop(ctx): # funci??n para parar el bot
    playing_audio = bot.playing_audio # obtiene el objeto de audio
    if playing_audio: # si el objeto de audio est?? activo
        player = playing_audio['player'] # obtiene el objeto de audio
        if player.is_playing(): # si el objeto de audio est?? activo
            player.pause() # pausa el objeto de audio

@bot.command()
async def resume(ctx): # funci??n para reanudar el bot
    playing_audio = bot.playing_audio # obtiene el objeto de audio
    if playing_audio: # si el objeto de audio est?? activo
        player = playing_audio['player'] # obtiene el objeto de audio
        if player.is_paused(): # si el objeto de audio est?? pausado
            player.resume() # reanuda el objeto de audio

@bot.command()
async def skip(ctx, amount: int = 1):
    if not ctx.voice_client: # si no esta conectado a un canal de voz
        return await ctx.send("No estoy conectado a un canal de voz.") # envia el mensaje de error

    if not cola_reproduccion: # si no hay canciones en la cola de reproducci??n
        return await ctx.send("No hay canciones en la cola de reproducci??n.") # envia un mensaje de error
    
    else: # si hay canciones en la cola de reproducci??n
        ctx.voice_client.stop() # parar el bot
        for i in range(amount - 1): # para cada canci??n en la cola de reproducci??n
            cola_reproduccion.get_nowait() # obtiene el siguiente elemento de la cola de reproducci??n y si no hay da una exepcion

        await ctx.send(f"Saltando la cancion.")

@bot.command()
async def hola(ctx):
    return await ctx.send("Hola gracias por usar mi bot!!")

@bot.command()
async def ayuda(ctx):
    return await ctx.send('Puedes usar los comandos:!play y la url de una cancion ,!stop frena la cancion,!resume resume la cancion,!skip salta la cancion,!conectar conectar a un canal de voz')

bot.run(TOKEN)



