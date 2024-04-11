xLLM6 is still under development. But a stable version is now availble in this folder, for one sub-LLM, with Python code and back-end tables. The differences with xLLM5 are explained in section C.4 (appendix), in the project textbook, <a href="https://github.com/VincentGranville/Large-Language-Models/blob/main/Projects4.pdf">here</a>. Download the PDF textbook and view it on a standard browser to activate all the clickable links and cross-references highlighted in red (internal references) or blue (external links). 

One main difference with xLLM5 is the introduction of x-embeddings, consisting of multi-token words. No other LLM has this unique feature, as far as I know. It is used to further enhance the quality of the results, and to facilitate the reconstruction of underlying (hidden) taxonomies, a core component of xLLM. Like xLLM5, the three programs are: 

<ul>
  <li><code>xllm6_util.py</code>: library with text processing functions, and to read the main tables</li>
  <li><code>xllm6_short.py</code>: main program for end-users, reads the tables produced by xllm6.py rather than creating them, and returns results to user queries (both on the screen and in a text file). </li>
  <li><code>xllm6.py</code>: main program for developpers, reads the crawled data, creates the tables, and returns results to user queries (both on the screen and in a text file)</li>
</ul>
