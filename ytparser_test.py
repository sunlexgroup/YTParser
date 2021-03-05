from ytparser import YTParser


requests_tuple = (
    'Python',
    'Программирование',
    'Спиннинг для джига'
)
browser = YTParser()
for query in requests_tuple:
    print(browser.get_overall_data(query, depth=20, depth_comments=50))
