Let's play a little game to give you an idea of how different algorithms for the same problem can have wildly different efficiencies. The computer is going to randomly select an integer from 1 to 15. You'll keep guessing numbers until you find the computer's number, and the computer will tell you each time if your guess was too high or too low:
Once you've found the number, reflect on what technique you used when deciding what number to guess next.

Maybe you guessed 1, then 2, then 3, then 4, and so on, until you guessed the right number. We call this approach **linear search**, because you guess all the numbers as if they were lined up in a row. It would work. But what is the highest number of guesses you could need? If the computer selects 15, you would need 15 guesses. Then again, you could be really lucky, which would be when the computer selects 1 and you get the number on your first guess. How about on average? If the computer is equally likely to select any number from 1 to 15, then on average you'll need 8 guesses.

But you could do something more efficient than just guessing 1, 2, 3, 4, …, right? Since the computer tells you whether a guess is too low, too high, or correct, you can start off by guessing 8. If the number that the computer selected is less than 8, then because you know that 8 is too high, you can eliminate all the numbers from 8 to 15 from further consideration. If the number selected by the computer is greater than 8, then you can eliminate 1 through 8. Either way, you can eliminate half the numbers. On your next guess, eliminate half of the remaining numbers. Keep going, always eliminating half of the remaining numbers.

We call this halving approach **binary search**, and no matter which number from 1 to 15 the computer has selected, you should be able to find the number in at most 4 guesses with this technique.

Here, try it for a number from 1 to 300. You should need no more than 9 guesses.
How many guesses did it take you to find the number this time? Why should you never need more than 9 guesses? (Can you think of a mathematical explanation)?

(created by Khan Academy: https://www.khanacademy.org/computing/computer-science/algorithms/intro-to-algorithms/a/a-guessing-game)