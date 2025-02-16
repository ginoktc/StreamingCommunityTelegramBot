import os
from typing import List

from dotenv import load_dotenv

from StreamingCommunity.Util.os import os_summary

## SUPER IMPORTANT
os_summary.get_system_summary()


from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
)


from StreamingCommunity.Api.Template.Class.SearchType import MediaItem
from StreamingCommunity.Api.Player.vixcloud import VideoSource
from StreamingCommunity.Api.Site.streamingcommunity import search
from StreamingCommunity.Api.Site.streamingcommunity.film import download_film as d_film
from StreamingCommunity.Api.Site.streamingcommunity.series import download_episode
from StreamingCommunity.Api.Site.streamingcommunity.costant import SITE_NAME
from StreamingCommunity.Api.Site.streamingcommunity.site import get_version_and_domain
from StreamingCommunity.Api.Site.streamingcommunity.util.ScrapeSerie import ScrapeSerie


# Bot token
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file.")

ALLOWED_USERS = [int(user_id) for user_id in os.getenv("ALLOWED_USERS").split(",")]


def restricted(func):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            update.message.reply_text(
                "🚫 Access denied: You are not authorized to use this bot."
            )
            return
        return func(update, context, *args, **kwargs)

    return wrapper


def get_year(date: str) -> str:
    """Return the year from a date string."""
    try:
        return date.split("-")[0]
    except IndexError:
        return ""


def get_number_of_seasons(media_item: MediaItem) -> int:
    """Get the number of seasons for a TV series."""
    version, domain = get_version_and_domain()

    scrape_serie = ScrapeSerie(SITE_NAME)
    video_source = VideoSource(SITE_NAME, True)

    # Setup video source
    scrape_serie.setup(version, media_item.id, media_item.slug)
    video_source.setup(media_item.id)

    # Collect information about seasons
    scrape_serie.collect_info_title()
    return scrape_serie.season_manager.seasons_count


def search_movie_or_tv(title) -> List[MediaItem]:
    results = search(title, get_onylDatabase=True)
    return results.media_list


def download_film(select_title: MediaItem) -> str:
    d_film(select_title)


def download_series_season(media_item: MediaItem, season_number: int):
    version, domain = get_version_and_domain()

    scrape_serie = ScrapeSerie(SITE_NAME)
    video_source = VideoSource(SITE_NAME, True)

    # Setup video source
    scrape_serie.setup(version, media_item.id, media_item.slug)
    video_source.setup(media_item.id)

    # Collect information about seasons
    scrape_serie.collect_info_title()
    scrape_serie.episode_manager.clear()
    scrape_serie.collect_info_season(season_number)

    download_episode(season_number, scrape_serie, video_source, download_all=True)


# Bot Handlers
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text(
        "Benvenut@! Scrivi il titolo di un film o di una serie TV."
    )


@restricted
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user input for search."""
    user_input = update.message.text
    await update.message.reply_text(f"Sto cercando: {user_input}...")
    results = search_movie_or_tv(user_input)

    results = results[:10]

    if not results or len(results) == 0:
        await update.message.reply_text(
            "Nessun risultato trovato. Riscrivi il messaggio /start e prova con una ricerca diversa."
        )
        return

    keyboard = []
    context.user_data["results"] = results
    for result in results:
        title = result.name
        media_type = result.type
        media_type_str = "Film" if media_type == "movie" else "Serie TV"
        result_id = result.id
        year = get_year(result.date)
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{title} ({media_type_str}) ({year})",
                    callback_data=f"{media_type}:{result_id}",
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Seleziona un risultato:", reply_markup=reply_markup
    )


@restricted
async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user selection from the search results."""
    query = update.callback_query
    await query.answer()

    media_type, item_id = query.data.split(":")
    search_results = context.user_data["results"]
    media_item = [item for item in search_results if item.id == int(item_id)][0]
    if media_type == "movie":
        await query.edit_message_text(
            "Download del film in corso, ti manderó un messaggio non appena avró finito!😘🏴‍☠️",
            reply_markup=None,
        )
        download_film(media_item)
        await query.message.reply_text("Download completato!")

    elif media_type == "tv":
        await query.edit_message_text(
            "Download delle informazioni in corso...", reply_markup=None
        )
        num_seasons = get_number_of_seasons(media_item)
        context.user_data["num_seasons"] = num_seasons

        keyboard = [
            [
                InlineKeyboardButton(
                    "Tutte le stagioni", callback_data=f"tv:{item_id}:all"
                )
            ]
        ]
        for season in range(1, num_seasons + 1):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"Stagione {season}",
                        callback_data=f"tv:{item_id}:{season}",
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Seleziona una stagione:", reply_markup=reply_markup
        )


@restricted
async def handle_season_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle season selection and simulate a loading bar."""
    query = update.callback_query
    await query.answer()

    _, tv_id, season = query.data.split(":")
    search_results = context.user_data["results"]
    media_item = [item for item in search_results if item.id == int(tv_id)][0]

    if season == "all":
        num_seasons = context.user_data["num_seasons"]
        for i in range(1, num_seasons + 1):
            # Remove the markup
            await query.message.reply_text(
                f"Download della stagione {i} in corso, ti manderó un messaggio non appena avró finito!😘🏴‍☠️",
                reply_markup=ReplyKeyboardRemove(),
            )
            download_series_season(media_item, i)
            await query.message.reply_text(f"Download della stagione {i} completato!")
    else:
        await query.message.reply_text(
            f"Download della stagione {season} in corso, ti manderó un messaggio non appena avró finito!😘🏴‍☠️",
            reply_markup=ReplyKeyboardRemove(),
        )
        download_series_season(media_item, int(season))
        await query.message.reply_text(f"Download della stagione {season} completato!")

    await query.message.reply_text("Download completato!")


# Main Function
def main():
    """Start the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)
    )
    application.add_handler(
        CallbackQueryHandler(handle_selection, pattern=r"^(movie|tv):\d+$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_season_selection, pattern=r"^tv:\d+:(all|\d+)$")
    )

    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
