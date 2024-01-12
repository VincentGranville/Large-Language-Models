<b>Important update</b>: <p>
<i>I don't plan on maintaing this folder moving forward. Instead, I built a more compact version, in particular with smaller tables. Both the code and the format of the tables have been streamlined and easier to understand, due to simplified architecture. The tables used in this folder are not compatible with those in the XLLM5 folder (the new version). For instance, instead of having hash of hash, hash of lists, and hash of lists of lists, the standard data sturcture in XLLM5 is hash of hash. For each keyword, repeated values present in various lists in LLM5 are bundled together with a count in XLLM5, in a hash rather than list structure.</i>

Currently, LLM-5.1 is a script (<code>LLM5.py</code>) processing all the webpages found in the Probability & Statistics category, on https://mathworld.wolfram.com/, to answer scientific questions in this field. The plan is to add other data sources in LLM-5.2 (my books, Wikipedia and so on), and offer a Web API or PyPi library. 

LLM-6 will cover all the math-related categories, with one set of tables per category. The plan is to also add AI and ML. Regardless of the version, the following applies:

<ul>
  <li> The <code>llm5_results.txt</code> file is an example of search results for a sample question. The <code>llm5_dump.txt</code> file contains the results for all potential queries with words up to 4 tokens, found in the crawling dictionary.</li>
  <li>All other <code>llm5_xxxx.txt</code> files are input files containing the minimum information for <code>LL5_short.py</code> (the short version of the script) to perform all the necessary tasks.</li>
</ul>

I am finishing the scripts LLM5.py and LLM5_short.py. I will upload them when they are sufficiently improved. I will also add some documentation.
