# Sports Market Terminal Feature Guide

This project is a Bloomberg-style market intelligence terminal for sports bettors. It combines stored demo markets, live MLB sportsbook odds, market movement, injury/news context, price comparison, opportunity ranking, bet tracking workflows, and an AI Copilot.

The app has two data modes:

- `Demo Mode`: uses stored sample odds across NBA, MLB, and NFL so the full product workflow is populated for demos.
- `Live Mode`: uses real MLB odds and injury/news ingestion from external APIs.

## 1. Demo Mode And Live Mode

The platform separates demo data from live data so users understand exactly what they are seeing.

Demo Mode is the default. It contains stored sample markets for:

- NBA
- MLB
- NFL

This mode is ideal for demos because charts, sportsbook comparison, signals, Copilot responses, and bet tracking workflows all have populated data.

Live Mode is an explicit opt-in mode for real MLB data. It uses API credits, so live refreshes are manual rather than automatic.

## 2. Multi-Sport Market Board

The main board shows games for the selected sport and data mode. Each game card includes the matchup, start time, current spread, opening spread, moneyline, total, opportunity score, and market regime tags.

The current demo board includes:

- 5 NBA games
- 4 MLB games
- 4 NFL games
- 1,040 stored demo odds snapshots

The board is designed to help a bettor quickly scan the full market and decide which games deserve attention. Instead of forcing the user to inspect every game manually, the terminal surfaces games with disagreement, stale prices, or other market signals.

## 3. Sport Tabs

The app includes top-level sport tabs:

- `NBA`
- `MLB`
- `NFL`

The selected sport controls the board, opportunity view, screener, notebook, tracking view, and Copilot context.

In Live Mode, the app currently focuses on MLB because the live odds ingestion endpoint fetches real MLB markets.

## 4. Opportunity Score

Each game receives an opportunity score. This score is calculated from signals such as price alerts, sportsbook disagreement, volatility, and warning-level market signals.

The purpose is not to guarantee a profitable bet. Instead, the score helps prioritize where to look first. A high score means the market is showing unusual behavior, such as a book offering a cheaper price than the broader market or sportsbooks disagreeing on the spread.

## 5. Market Regime Tags

Games are labeled with quick market regime tags:

- `Stale Price`
- `High Disagreement`
- `Volatile`
- `Signal Active`
- `Quiet Market`

These tags summarize the state of the market in plain language. For a demo, this is useful because it shows the platform is not only displaying odds but interpreting the betting market.

## 6. Terminal Command Bar

The header includes a terminal-style command/search bar. Users can search for teams or type commands to jump between views.

Supported commands include:

- `BOARD`, `MLB`, `GAMES`: opens the main board
- `OPP`, `OPPORTUNITIES`, `EV`, `STEAM`: opens the opportunities view
- `WATCH`, `WATCHLIST`, `PINNED`: opens the watchlist
- `NOTEBOOK`, `BETS`, `IDEAS`: opens saved bet ideas
- `TRACK`, `TRACKING`, `CLV`, `PERFORMANCE`: opens the CLV tracking view
- `SCREEN`, `SCREENER`, `FILTER`, `FILTERS`: opens the market screener
- `COPILOT`, `CHAT`, `AI`, `ASSISTANT`: opens the Copilot view

The command bar makes the app feel more like a professional terminal than a normal dashboard.

## 7. Keyboard Shortcuts

The platform supports power-user keyboard shortcuts:

- `/`: focus the command bar
- `B`: open Board
- `O`: open Opportunities
- `W`: open Watchlist
- `N`: open Notebook
- `T`: open Tracking
- `S`: open Screener
- `C`: open Copilot
- `Esc`: leave game detail or unfocus search

These shortcuts help the product feel fast and terminal-like during a demo.

## 8. Top Opportunities View

The Opportunities tab shows a ranked table of the best current market spots. It includes:

- game
- opportunity score
- best available moneyline
- best price alert
- top reason the game is interesting

This view is useful for answering: “Where should a bettor look first?” It turns the platform from a passive odds board into a decision-support tool.

## 9. Market Screener

The Screener tab lets the user filter the slate by market condition. Instead of scrolling every game, the user can narrow the board to the exact type of opportunity they care about.

Current screener filters include:

- `Stale Price`
- `High Disagreement`
- `Starts Soon`
- `Watchlist`
- `Saved Ideas`
- `Quiet Market`

The screener table shows the game, start time, market regime, opportunity score, best alert, and whether the game is pinned or has saved bet ideas. This gives the platform a more professional terminal workflow because the user can slice the slate by signal type.

## 10. Manual Data Refresh Controls

The header includes mode-aware manual refresh controls.

In Demo Mode, the button is:

- `Reset Demo Data`

This calls the backend demo reset endpoint and restores the stored sample market.

In Live Mode, the app shows:

- `Refresh Live MLB Odds`
- `Refresh Injuries & News`

`Refresh Live MLB Odds` calls the backend Odds API ingestion endpoint only when the user clicks it.

`Refresh Injuries & News` calls the SportsDataIO context ingestion endpoint and then reloads the selected game's context if the user is on a game detail page.

This is intentionally manual because the current Odds API plan has limited credits. The platform does not automatically spend credits in the background. After a refresh completes, the board and freshness metadata update.

The app avoids displaying noisy backend ingestion messages in the main content area so the demo flow stays clean.

## 11. Odds Freshness Indicator

The header shows how fresh the stored odds are. It displays the age of the most recent odds snapshot, such as `Odds 12m ago` or `Odds 5h 0m ago`.

The platform also stores and exposes:

- latest snapshot timestamp
- age in seconds
- sportsbook count
- total snapshot count

This matters because market intelligence is only useful if the user knows whether the odds are current. During a demo, this is a good moment to explain that the app is credit-conscious but ready for automated refresh later.

## 12. Game Detail Page

Clicking any game opens a game-specific detail page. This page brings together the market, quant tools, line movement, injuries/news, and sportsbook comparison for one matchup.

The top section includes:

- matchup
- start time
- market regime tags
- spread
- opening spread
- moneyline
- total
- watchlist button

This page is the core “single-game terminal” experience.

## 13. Selectable Line Movement Chart

The line movement chart lets the user switch between:

- home spread
- moneyline
- total

Each sportsbook is plotted separately. This allows the user to inspect whether books are moving together or whether one book is lagging.

Demo Mode uses preloaded historical snapshots so line charts are populated immediately. Live Mode becomes more powerful as more live odds snapshots are collected over time.

## 14. Market Signals Panel

The Market Signals panel displays detected signals for the selected game. These signals are intended to highlight conditions like sharp movement, book disagreement, volatility, or other market behaviors.

The product currently has the signal framework in place, and this can be expanded as more historical odds snapshots are collected.

## 15. Quant Snapshot

The Quant Snapshot is a betting-focused analytics panel. It includes:

- best available prices
- no-vig moneyline probabilities
- EV calculator
- price alerts

This is one of the most important parts of the platform because it translates raw odds into actionable market intelligence.

## 16. Best Available Prices

The platform compares sportsbook prices and identifies the best available price for each market/selection.

For example, if multiple sportsbooks offer a moneyline on the same team, the system highlights which book has the best current number.

This is valuable because sports bettors can improve expected return simply by consistently taking the best available price.

## 17. No-Vig Moneyline Probabilities

The platform calculates no-vig fair probabilities from available moneyline markets.

Sportsbook odds include margin, also called vig. The no-vig calculation removes that margin to estimate the market’s implied fair probability for each team.

This helps the user compare their own opinion against the market. If the user believes a team wins more often than the no-vig probability suggests, the bet may deserve further evaluation.

## 18. EV Calculator

The EV calculator lets a user enter their own estimated win probability for a moneyline side. The platform then calculates:

- expected value per `$100`
- edge versus the sportsbook price
- quarter-Kelly stake percentage

This is the first step toward identifying potential positive-EV bets. The platform does not claim a bet is profitable by itself; it gives the user the tools to compare their probability estimate to the available market price.

## 19. Quarter-Kelly Sizing

The EV calculator includes quarter-Kelly sizing. Kelly sizing estimates how much of a bankroll to risk based on edge and payout.

The platform uses quarter Kelly rather than full Kelly because full Kelly can be aggressive. This gives a more conservative risk-management signal.

## 20. Price Alerts

Price alerts identify cases where one sportsbook appears cheaper than the market average on an implied probability basis.

Instead of comparing American odds directly, the system compares implied probability. This avoids misleading results when prices cross from negative to positive odds.

These alerts help identify potentially stale or lagging sportsbook prices.

## 21. Line Movement Alerts

The platform can compare the first stored snapshot against the latest stored snapshot and flag material movement.

It currently detects:

- at least `0.5` points of line movement
- at least `15` cents of odds movement

This feature becomes more useful as more odds snapshots are stored over time.

## 22. Injuries & News Panel

The game detail page includes injury and news context for the teams in the selected game.

This panel shows:

- recent injury report changes
- current player injuries
- news updates

SportsDataIO trial data may scramble some injury fields, so the frontend and backend avoid showing scrambled values. This keeps the demo cleaner and more professional.

## 23. Injury Change Detection

The backend tracks injury events. If a player appears on the injury report for the first time, the system records a new injury event. If a player’s status, body part, or note changes, the system records an update event.

This matters because sports betting markets often react quickly to injury news. Over time, this can support news-to-price impact analysis.

## 24. Bet Idea Notebook

The platform includes a local Bet Idea Notebook. From a game detail page, a user can save a bet idea with:

- game
- market
- selection
- line
- sportsbook
- odds
- user probability
- EV per `$100`
- quarter-Kelly stake
- notes/thesis
- timestamp

This turns the platform into a workflow tool rather than only an odds display.

## 25. Notebook View

The Notebook tab shows all saved bet ideas. Each saved idea includes the key betting metrics and the user’s notes.

Users can click a saved idea to return to the associated game or delete ideas they no longer want to track.

For a demo, this is useful because it shows how a bettor can form, save, and revisit a thesis.

## 26. Watchlist

Users can pin games to a watchlist using the star button. The Watchlist tab shows only pinned games.

This is useful for bettors who want to monitor a few games closely instead of scanning the full slate repeatedly.

The current implementation stores the watchlist in browser local storage.

## 27. CLV Tracking

The Tracking tab compares saved bet ideas against the latest available market price.

For each saved idea, it shows:

- saved price
- current best matching price
- CLV in cents
- whether the saved idea is beating the current market
- associated thesis note

CLV means closing line value. Right now, the system compares saved price versus the latest available price. Once the app stores closing prices, this same view can become a true closing-line-value tracker.

## 28. Average CLV

The top stats include average CLV across saved bet ideas with a current matching price.

This gives the user a quick sense of whether their saved bets are generally moving in their favor.

In the future, this can become one of the most important performance metrics in the app.

## 29. Sportsbook Matrix

Each game detail page includes a sportsbook comparison matrix. Rows are markets/selections, and columns are sportsbooks.

The best available price in each row is highlighted.

This is one of the most terminal-like features because it gives a dense, professional view of book-by-book market differences.

## 30. Full Odds Table

The detail page also includes a full odds table with:

- sportsbook
- market
- selection
- line
- odds
- implied probability

This gives the user a complete raw view behind the higher-level summaries.

## 31. AI Market Copilot

The Copilot tab provides an AI assistant that explains the current market context.

It can answer questions such as:

- Which games should I inspect first?
- Why is this opportunity score high?
- Where are books disagreeing?
- How should I interpret no-vig probabilities?
- What does the EV calculator imply?
- What changed in the line movement?

The Copilot is context-aware. It receives:

- selected sport
- selected data mode
- current board context
- selected game context when available
- price alerts
- signals
- no-vig probabilities
- movement alerts

The Copilot is not intended to guarantee picks. It explains market information already present in the platform.

## 32. The Odds API Integration

The platform can ingest MLB odds from The Odds API. It normalizes sportsbook odds into the app’s internal database format.

The integration currently supports:

- moneyline
- spreads
- totals
- multiple sportsbooks
- implied probability calculation
- timestamped odds snapshots

Due to limited credits, the app avoids unnecessary API calls unless explicitly triggered through backend ingestion.

## 33. SportsDataIO Injury/News Integration

The platform also integrates SportsDataIO for MLB player context.

This is currently used for:

- injured players
- player/team news
- injury event detection

Because SportsDataIO trial data may include scrambled values, the platform filters those fields out before displaying them.

## 34. Current Storage Model

The backend database stores:

- teams
- games
- sportsbooks
- odds snapshots
- market signals
- player injuries
- player news
- injury events

Frontend local storage currently stores:

- watchlist
- saved bet ideas

## 37. Future Features

The strongest future additions are:

- automated odds snapshot collection
- true closing-line tracking
- signal performance analytics
- sharper fair-line model
- injury/news-to-price impact timeline
- player props and alternate markets
- backend persistence for user notebooks/watchlists
- account-based saved bet history
- broader live support beyond MLB

These future additions would move the platform closer to a true professional betting terminal.
