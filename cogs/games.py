"""
BEN Discord Bot - Interactive UI Games Engine
Featuring Tic-Tac-Toe (Button Grid), Rock-Paper-Scissors, High-Stakes Slots, Trivia, and Dice.
Styled with sleek transparent embeds (#2B2D31).
"""
import random
import asyncio
from typing import Optional, List
import discord
from discord import app_commands, ui
from discord.ext import commands
from utils.embeds import BenEmbed, success_embed, error_embed, info_embed
import config

# ==========================================
# 1. TIC-TAC-TOE (Interactive 3x3 Button Grid)
# ==========================================
class TicTacToeButton(ui.Button["TicTacToeView"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToeView = self.view

        if interaction.user != view.current_player:
            await interaction.response.send_message("❌ It is not your turn!", ephemeral=True)
            return

        if view.board[self.y][self.x] != 0:
            await interaction.response.send_message("❌ That tile is already taken!", ephemeral=True)
            return

        if view.current_player == view.player_x:
            self.style = discord.ButtonStyle.primary
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = 1
            view.current_player = view.player_o
            content = f"🎮 **Turn**: {view.player_o.mention} (`O`)"
        else:
            self.style = discord.ButtonStyle.danger
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = 2
            view.current_player = view.player_x
            content = f"🎮 **Turn**: {view.player_x.mention} (`X`)"

        winner = view.check_winner()
        if winner:
            view.stop_game()
            if winner == 1:
                result_text = f"🏆 **Victory!** {view.player_x.mention} (`X`) has won the match!"
                color = config.COLOR_PRIMARY
            elif winner == 2:
                result_text = f"🏆 **Victory!** {view.player_o.mention} (`O`) has won the match!"
                color = config.COLOR_ERROR
            else:
                result_text = "🤝 **Match Drawn!** Neither player could achieve victory."
                color = config.COLOR_WARNING

            embed = BenEmbed(
                title="🎮  TIC-TAC-TOE • GAME OVER",
                description=result_text,
                color=color,
                footer_text=f"Match: {view.player_x.name} vs {view.player_o.name}"
            )
            await interaction.response.edit_message(content=None, embed=embed, view=view)
            return

        await interaction.response.edit_message(content=content, view=view)


class TicTacToeView(ui.View):
    def __init__(self, player_x: discord.Member, player_o: discord.Member):
        super().__init__(timeout=180)
        self.player_x = player_x
        self.player_o = player_o
        self.current_player = player_x
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def stop_game(self):
        for child in self.children:
            child.disabled = True

    def check_winner(self) -> int:
        # Check rows & columns
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != 0:
                return self.board[i][0]
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != 0:
                return self.board[0][i]

        # Diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]

        # Check full board (tie)
        if all(cell != 0 for row in self.board for cell in row):
            return 3

        return 0


# ==========================================
# 2. ROCK-PAPER-SCISSORS (UI Buttons)
# ==========================================
class RPSView(ui.View):
    def __init__(self, player: discord.Member, opponent: Optional[discord.Member] = None):
        super().__init__(timeout=60)
        self.player = player
        self.opponent = opponent
        self.choices = {}

    CHOICES = {
        "rock": {"name": "Rock", "emoji": "🪨", "beats": "scissors"},
        "paper": {"name": "Paper", "emoji": "📄", "beats": "rock"},
        "scissors": {"name": "Scissors", "emoji": "✂️", "beats": "paper"}
    }

    async def handle_choice(self, interaction: discord.Interaction, choice: str):
        user = interaction.user
        if self.opponent is None:
            # Playing against AI
            if user != self.player:
                await interaction.response.send_message("This is not your game!", ephemeral=True)
                return

            bot_choice = random.choice(["rock", "paper", "scissors"])
            player_data = self.CHOICES[choice]
            bot_data = self.CHOICES[bot_choice]

            if choice == bot_choice:
                verdict = "🤝 **It's a Stalemate (Draw)!**"
                color = config.COLOR_WARNING
            elif player_data["beats"] == bot_choice:
                verdict = f"🏆 **You Won!** {player_data['emoji']} crushes {bot_data['emoji']}"
                color = config.COLOR_SUCCESS
            else:
                verdict = f"💀 **BEN Wins!** {bot_data['emoji']} overpowers {player_data['emoji']}"
                color = config.COLOR_ERROR

            embed = BenEmbed(
                title="🎮  ROCK-PAPER-SCISSORS",
                description=(
                    f"{verdict}\n\n"
                    f"{config.EMOJIS['bullet']} **Your Pick**: {player_data['emoji']} `{player_data['name']}`\n"
                    f"{config.EMOJIS['bullet']} **BEN's Pick**: {bot_data['emoji']} `{bot_data['name']}`\n"
                ),
                color=color
            )
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # 2 Player Mode
            if user not in (self.player, self.opponent):
                await interaction.response.send_message("You are not part of this duel!", ephemeral=True)
                return
            if user.id in self.choices:
                await interaction.response.send_message("You have already locked in your weapon!", ephemeral=True)
                return

            self.choices[user.id] = choice
            await interaction.response.send_message(f"🔒 Locked in your pick: **{choice.capitalize()}**!", ephemeral=True)

            if len(self.choices) == 2:
                p1_choice = self.choices[self.player.id]
                p2_choice = self.choices[self.opponent.id]
                p1_data = self.CHOICES[p1_choice]
                p2_data = self.CHOICES[p2_choice]

                if p1_choice == p2_choice:
                    res = "🤝 **Match Drawn!** Both picked identical moves."
                    color = config.COLOR_WARNING
                elif p1_data["beats"] == p2_choice:
                    res = f"🏆 **Winner**: {self.player.mention}!"
                    color = config.COLOR_SUCCESS
                else:
                    res = f"🏆 **Winner**: {self.opponent.mention}!"
                    color = config.COLOR_SUCCESS

                embed = BenEmbed(
                    title="🎮  ROCK-PAPER-SCISSORS • DUEL COMPLETE",
                    description=(
                        f"{res}\n\n"
                        f"{config.EMOJIS['bullet']} {self.player.mention}: {p1_data['emoji']} `{p1_data['name']}`\n"
                        f"{config.EMOJIS['bullet']} {self.opponent.mention}: {p2_data['emoji']} `{p2_data['name']}`\n"
                    ),
                    color=color
                )
                for child in self.children:
                    child.disabled = True
                await interaction.message.edit(embed=embed, view=self)

    @ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.secondary)
    async def rock_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_choice(interaction, "rock")

    @ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.secondary)
    async def paper_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_choice(interaction, "paper")

    @ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def scissors_btn(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_choice(interaction, "scissors")


# ==========================================
# 3. TRIVIA (Interactive Multiple Choice)
# ==========================================
TRIVIA_QUESTIONS = [
    {
        "q": "What is the native background hex code of Discord Dark Theme?",
        "options": ["#2B2D31", "#1E1F22", "#313338", "#232428"],
        "correct": "#2B2D31",
        "category": "Technology"
    },
    {
        "q": "Which programming language was originally called Oak?",
        "options": ["Python", "Java", "Ruby", "C++"],
        "correct": "Java",
        "category": "Coding"
    },
    {
        "q": "Which planet is known as the Red Planet?",
        "options": ["Venus", "Mars", "Jupiter", "Saturn"],
        "correct": "Mars",
        "category": "Science"
    },
    {
        "q": "In computer science, what does 'RAM' stand for?",
        "options": ["Random Access Memory", "Read All Memory", "Rapid Action Module", "Real-time Access Media"],
        "correct": "Random Access Memory",
        "category": "Technology"
    },
    {
        "q": "What is the capital city of Japan?",
        "options": ["Kyoto", "Osaka", "Tokyo", "Yokohama"],
        "correct": "Tokyo",
        "category": "Geography"
    },
    {
        "q": "Who is credited with creating the Linux operating system kernel?",
        "options": ["Linus Torvalds", "Steve Wozniak", "Guido van Rossum", "Dennis Ritchie"],
        "correct": "Linus Torvalds",
        "category": "Tech History"
    }
]

class TriviaChoiceButton(ui.Button):
    def __init__(self, option_text: str, is_correct: bool, row: int):
        super().__init__(label=option_text[:80], style=discord.ButtonStyle.secondary, row=row)
        self.option_text = option_text
        self.is_correct = is_correct

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TriviaView = self.view

        if interaction.user != view.player:
            await interaction.response.send_message("❌ This is not your trivia session!", ephemeral=True)
            return

        for child in view.children:
            if isinstance(child, TriviaChoiceButton):
                child.disabled = True
                if child.is_correct:
                    child.style = discord.ButtonStyle.success
                elif child == self:
                    child.style = discord.ButtonStyle.danger

        if self.is_correct:
            result = f"🎉 **Correct Answer!** You scored points."
            color = config.COLOR_SUCCESS
        else:
            result = f"❌ **Incorrect!** The correct answer was **{view.correct_answer}**."
            color = config.COLOR_ERROR

        embed = BenEmbed(
            title="🧠  TRIVIA CHALLENGE • RESULT",
            description=f"{result}\n\n**Question**: {view.question_text}",
            color=color
        )
        await interaction.response.edit_message(embed=embed, view=view)
        view.stop()


class TriviaView(ui.View):
    def __init__(self, player: discord.Member, question_data: dict):
        super().__init__(timeout=45)
        self.player = player
        self.question_text = question_data["q"]
        self.correct_answer = question_data["correct"]

        options = question_data["options"].copy()
        random.shuffle(options)

        for i, opt in enumerate(options):
            self.add_item(TriviaChoiceButton(opt, opt == self.correct_answer, row=i // 2))


# ==========================================
# GAMES COG
# ==========================================
class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="tictactoe", description="Challenge another server member to an interactive 3x3 Tic-Tac-Toe duel")
    @app_commands.describe(opponent="The player you want to challenge")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent == interaction.user:
            await interaction.response.send_message("You cannot challenge yourself!", ephemeral=True)
            return
        if opponent.bot:
            await interaction.response.send_message("Bots do not play Tic-Tac-Toe!", ephemeral=True)
            return

        view = TicTacToeView(player_x=interaction.user, player_o=opponent)
        embed = BenEmbed(
            title="🎮  TIC-TAC-TOE MATCH",
            description=(
                f"### Duel Initiated! ✦\n"
                f"{config.EMOJIS['bullet']} **Player X**: {interaction.user.mention}\n"
                f"{config.EMOJIS['bullet']} **Player O**: {opponent.mention}\n\n"
                f"> First Turn: {interaction.user.mention} (`X`)\n"
                f"> Tap an open square on the grid to place your mark."
            ),
            color=config.COLOR_TRANSPARENT
        )
        await interaction.response.send_message(
            content=f"{interaction.user.mention} challenged {opponent.mention}!",
            embed=embed,
            view=view
        )

    @app_commands.command(name="rps", description="Play Rock-Paper-Scissors against BEN AI or another member")
    @app_commands.describe(opponent="Optional member to challenge. Leave blank to play against BEN AI")
    async def rps(self, interaction: discord.Interaction, opponent: Optional[discord.Member] = None):
        if opponent and opponent == interaction.user:
            await interaction.response.send_message("You cannot duel yourself!", ephemeral=True)
            return
        if opponent and opponent.bot:
            opponent = None  # Play against BEN AI directly

        view = RPSView(player=interaction.user, opponent=opponent)
        mode = f"Duel: {interaction.user.mention} vs {opponent.mention}" if opponent else f"Duel: {interaction.user.mention} vs **BEN AI**"

        embed = BenEmbed(
            title="🎮  ROCK-PAPER-SCISSORS",
            description=(
                f"### {mode} ✦\n"
                f"> Select your secret weapon below.\n"
                f"{'> Both players must click a button to lock their move.' if opponent else '> BEN AI will instantly counter-pick!'}"
            ),
            color=config.COLOR_TRANSPARENT
        )
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="trivia", description="Answer multiple-choice trivia questions with interactive buttons")
    async def trivia(self, interaction: discord.Interaction):
        q_data = random.choice(TRIVIA_QUESTIONS)
        view = TriviaView(player=interaction.user, question_data=q_data)

        embed = BenEmbed(
            title=f"🧠  TRIVIA: {q_data['category'].upper()}",
            description=(
                f"### {q_data['q']} ✦\n\n"
                f"> *Select the correct button below before the 45-second timer expires!*"
            ),
            color=config.COLOR_TRANSPARENT,
            footer_text=f"Requested by {interaction.user.name} • 4 Choices"
        )
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="slots", description="Spin the high-roller slot machine")
    @app_commands.describe(bet="Tokens to bet (default 100)")
    async def slots(self, interaction: discord.Interaction, bet: int = 100):
        if bet < 1:
            await interaction.response.send_message("Bet must be at least 1 token.", ephemeral=True)
            return

        symbols = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
        # Spin 3 reels
        r1, r2, r3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)

        if r1 == r2 == r3:
            if r1 == "💎":
                multiplier = 50
                title = "💎 JACKPOT DIAMOND ROYALE! 💎"
            elif r1 == "7️⃣":
                multiplier = 25
                title = "🔥 LUCKY SEVEN TRIFECTA! 🔥"
            else:
                multiplier = 10
                title = "🎉 TRIPLE MATCH WIN! 🎉"
            winnings = bet * multiplier
            color = config.COLOR_SUCCESS
            status = f"**MASSIVE WIN!** You won **+{winnings:,}** tokens! ({multiplier}x)"
        elif r1 == r2 or r2 == r3 or r1 == r3:
            multiplier = 2
            winnings = bet * multiplier
            color = config.COLOR_WARNING
            title = "✨ DOUBLE MATCH! ✨"
            status = f"**Nice hit!** You won **+{winnings:,}** tokens! ({multiplier}x)"
        else:
            winnings = 0
            color = config.COLOR_ERROR
            title = "💀 NO MATCH - HOUSE WINS"
            status = f"Better luck next spin! You lost **-{bet:,}** tokens."

        embed = BenEmbed(
            title=title,
            description=(
                f"```\n"
                f"  ╔═════════════════╗\n"
                f"  ║   {r1} │ {r2} │ {r3}   ║\n"
                f"  ╚═════════════════╝\n"
                f"```\n"
                f"{status}\n\n"
                f"{config.EMOJIS['bullet']} **Wager**: `{bet:,}` tokens\n"
                f"{config.EMOJIS['bullet']} **Outcome**: `{winnings:,}` tokens\n"
            ),
            color=color,
            footer_text=f"BEN Casino • Player: {interaction.user.name}"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a fair weighted coin with visual result")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        icon = "🪙" if result == "Heads" else "🦅"
        embed = BenEmbed(
            title=f"🪙  COIN TOSS: {result.upper()}",
            description=(
                f"The coin landed firmly on **{result}**! {icon}\n\n"
                f"{config.EMOJIS['bullet']} **Result**: `{result}`\n"
                f"{config.EMOJIS['bullet']} **Probability**: `50.00%`"
            ),
            color=config.COLOR_TRANSPARENT
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Roll a polyhedral die (e.g. d6, d20, d100)")
    @app_commands.describe(sides="Number of sides on the die (default 6)")
    async def dice(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2 or sides > 1000:
            await interaction.response.send_message("Sides must be between 2 and 1000.", ephemeral=True)
            return
        roll = random.randint(1, sides)
        embed = BenEmbed(
            title=f"🎲  DIE ROLL: d{sides}",
            description=(
                f"You rolled a **{roll}** on a d{sides}!\n\n"
                f"{config.EMOJIS['bullet']} **Rolled**: `{roll}` / `{sides}`\n"
                f"{config.EMOJIS['bullet']} **Critical**: `{'Yes! Max Roll!' if roll == sides else 'No'}`"
            ),
            color=config.COLOR_TRANSPARENT
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
