# test_bbcode_bold
# input: "[b]hello[/b]"
# assert: "<strong>hello</strong>" in result

# test_bbcode_italic
# input: "[i]hello[/i]"
# assert: "<em>hello</em>" in result

# test_bbcode_underline
# input: "[u]hello[/u]"
# assert: "text-decoration:underline" in result

# test_bbcode_strikethrough
# input: "[s]hello[/s]"
# assert: "<del>hello</del>" in result

# test_bbcode_code
# input: "[code]print('hi')[/code]"
# assert: "<pre><code>" in result

# test_bbcode_quote
# input: "[quote]some text[/quote]"
# assert: "<blockquote>" in result

# test_bbcode_quote_with_author
# input: "[quote=ms_johnson]great question[/quote]"
# assert: "<cite>ms_johnson</cite>" in result

# test_bbcode_url
# input: "[url]https://example.com[/url]"
# assert: 'href="https://example.com"' in result

# test_bbcode_url_with_label
# input: "[url=https://example.com]click here[/url]"
# assert: "click here" in result, 'href="https://example.com"' in result

# test_bbcode_url_blocks_javascript
# input: "[url]javascript://evil[/url]"
# assert: "javascript:" not in result

# test_bbcode_list
# input: "[list][*]item one[*]item two[/list]"
# assert: "<ul>" in result, "<li>item one</li>" in result

# test_bbcode_empty
# input: ""
# assert: result == ""

# test_bbcode_newlines_become_br
# input: "line one\nline two"
# assert: "<br>" in result

# test_bbcode_xss_in_url
# input: '[url=javascript:alert(1)]click[/url]'
# assert: "javascript:" not in result
