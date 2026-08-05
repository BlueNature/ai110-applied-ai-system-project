# RAGuesser Model Card

---

## 1) Summary

RAGuesser is an interactive game in which users guess a number from a set range. They receive clues on whether their guess was too high or too low, and can use those clues to approach the correct answer. Additionally, the game uses RAG to create feedback for the player tailored to their previous guesses and the current state of the game.

---

## 2) Limitations and Potential Biases

The biggest potential issue I can think of is over-reliance on the retrieved documents. I have to wonder if this is an issue with all RAG systems. I think it is, actually, because one common flaw is that if the documents are inaccurate or outdated, and the AI is relying on those, then so too will its output be. In a game such as this, it usually isn't a big issue since the game is simple and widespread enough that the AI will also have knowledge about how to play the game and certain strategies in its general training data; however, if this was a more specialized game for which training data doesn't exist, then it really depends on the quality of the documents.

Not only is RAG limited by the quality of its documents, but it can also inherit biases found within those documents. If one article was written by a person who wants to promote their own algorithm that runs in O(n!) time, and the AI picks up on it, then it will pass that information on to the user. (This is not an issue here where documents have been hand-selected, but it is in places where such selection criteria are not as doable, such as Google's AI overview.) For a more pernicious example, consider an article written by a casino asserting that gambler's fallacy really isn't that bad.

We are telling the AI to draw on what it has in the retrieved documents, and not to apply its own judgement on whether those facts are accurate or helpful. However, in many cases we can't simply tell it to apply its own judgement, because there is not enough general training data for the AI to be able to make a judgement.

---

## 3) Ethics and Potential for Misuse

How would an AI that teaches you how to guess numbers possibly raise ethical issues? It probably doesn't, but that's because the scope is way too narrow. We have to think about more substantial ways this sort of AI is being used right now—particularly AI in education.

I have seen and even engaged with AI chatbots in educational tools throughout many places. One of the biggest ethical questions people initially ask is whether they will undermine or replace teachers. (In fact, this one might be too big for me to discuss here.) Another question that begs to be asked is how accurate AI can really be, since it is a well-known and fundamental fact that chatbots often hallucinate and make erroneous calculations. For example, if you had the AI for this game suggest the best next guess, it might not be correct 100% of the time. Additionally, even with RAG, the AI can still misinterpret or lose context relating to the retrieved documents, thus conveying them inaccurately. You could also intentionally make a harmful educational AI by imbuing it with inaccurate documents or having it bias a certain viewpoint or company. One of the biggest things to consider with AI in education is that people are using it to learn, so they have a more limited ability to check output; therefore, it is increasingly important that the output is accurate.

---

## 4) Unexpected Developments

Since I couldn't do much testing due to wanting to save my API calls, I implemented most of it with basic features. I didn't even test the prompts that much, apart from occasionally copying them into a free chatbot to get a general idea of what the response might look like. For the keyword-generation AI, I explained that it could phrase its output as a set of keywords, realistic questions a user might ask, prompts, or a combination of all three, but it appeared to choose the former consistently. I was also surprised to see the structure the chatbot often applied when creating the final feedback. It starts by introducing itself as RAGuesser and reviews the current game state with the user; even though this is not needed, it might give the user some reassurance that the AI's output is actually tailored to their play. Overall, though, it was basically just an instance of how LLM output can be unpredictable.

---

## 5) Collaboration Process with AI

Claude tried to `echo` my API key.

In all seriousness, of course there were some times that I pushed back on my AI coding agent's suggestions. Sometimes I used plan mode to go through an entire feature implementation, and it got stuck on the testing step. At one point it tried to open its own server to verify the code works, but I decided to have it stop since it was running into issues, plus I can easily do the same myself. (Maybe an important part of coding with AI agents is understanding when you can or should do certain things yourself) Similarly, I often looked through commands before running them since they occasionally seemed complicated and I wanted to make sure they were accomplishing the correct goals and not something else.

In many places, though, the AI was helpful. Because I still do not have fluent knowledge of Streamlit, having the AI help me with that part made things easier. It is also very helpful for creating test cases once you have sufficiently figured out what you need to test. In all cases, I still looked through the code myself. Ideally, I want to be able to not just understand it, but explain it myself. If I can't, I'll ask the AI what this code or command does before allowing it to proceed.

---

## 6) Reflection

One thing this project showed me is how things that seem complicated can actually be relatively simple to implement. I was under the impression that RAG was a very complex process, when in reality it can be boiled down to "match words in text and add then that text to the prompt". Of course, there is a lot of detail put into exactly how words are matched and sorted, and that part is what makes RAG so complex, but the basis of it is simple.

Finally, I am proud of the way I worked with AI for this project. When I expressed my concerns about spending a lot of time on these projects, I was told by one of the CodePath staff members about how realistically, you'll rarely be able to design everything to your specifications. I certainly have some things in mind that I might want to improve if I had more time, but oftentimes it's better to get something to a point where you can ship it instead of going into the territory of diminishing returns. Moreover, I am proud to see that I have learned how to use AI for coding without having it take over completely. While I am still wary to make sure that using AI does not atrophy my own skills as a programmer, I have been able to use it to write code while being in charge of the underlying design decisions and making sure I sufficiently understand the code myself instead of blindly trusting AI.
