XLLM stands for <b>Extreme LLM</b>, with faster execution, smaller tables, simplified architecture, and better results.

Python code:
<ul>
  <li><code>xllm5_util.py</code>: library with text processing functions, and to read the main tables</li>
  <li><code>xllm5_short.py</code>: main program for end-users, reads the tables produced by xllm5.py rather than creating these tables, and returns results to user queries (both on the screen and in a text file). </li>
  <li><code>xllm5.py</code>: main program for developpers, reads the crawled data, creates the tables, and returns results to user queries (both on the screen and in a text file)</li>
</ul>
