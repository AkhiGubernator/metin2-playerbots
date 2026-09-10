# =============================================================================
#  ItemShop -- standalone PHP web shop, buys write into player.item_award so
#  the stock delivery pipeline (ItemAwardManager.cpp) hands items to the
#  player next login. Independent login form against account.account, not the
#  retail sas/pid auto-login scheme -- real game credentials work.
# =============================================================================
# Pinned to bookworm and built without apt: the trixie tag's apt verifies
# InRelease with sequoia and failed on a player's Docker Desktop ("Splitting
# of clearsigned file failed as it doesn't contain all expected parts"), which
# cancelled the whole compose build and left him on the old server. Nothing
# here needs a Debian package - the healthcheck asks PHP itself.
FROM php:8.2-apache-bookworm

RUN docker-php-ext-install mysqli

COPY app/ /var/www/html/

# ACMD(do_in_game_mall) hardcodes "http://host/ishop?pid=...&sas=..." (no
# trailing slash). mod_dir's default DirectorySlash would 302 that to
# "/ishop/?pid=...&sas=..." before it ever reaches index.php - fine in a
# normal browser, but doubles the round trips through the old in-game
# embedded browser and made the shop intermittently fail to open
# ("Nie mozna odnalezc strony") instead of just being a bit slower. Serving
# /ishop directly avoids the extra hop entirely.
RUN a2enmod rewrite \
 && sed -i '/<VirtualHost \*:80>/a\    RewriteEngine On\n    RewriteRule ^/ishop$ /ishop/index.php [L]' \
    /etc/apache2/sites-enabled/000-default.conf

EXPOSE 80/tcp

HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
    CMD php -r 'exit(@file_get_contents("http://127.0.0.1/itemshop/") === false ? 1 : 0);'
