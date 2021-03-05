import os
import time
from sys import platform

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class YTParser:

    def __init__(self):
        self.__url = 'https://youtube.com/'
        self.__driver_path = self.__get_driver_path()
        self.__browser_instance = self.__create_browser_instance()
        self.__actions = ActionChains(self.__browser_instance)

    def __get_common_data_from_video(self,
                                     video: object,
                                     query: str,
                                     position: int) -> dict:
        """Извлекает необходимые данные из одного блока видео поисковой выдачи

        Args:
            video (object): Объект видео из поисковой выдачи по
            поисковому запросу
            query (str): поисковый запрос
            position (int): Позиция в поиске

        Returns:
            dict: Возвращает словарь из нужных данных
        """
        return dict(
            position=position+1,
            title=video.find_element_by_id('video-title').text,
            query=query,
            description=video.find_element(By.ID, 'description-text').text,
            link=video.find_element(
                By.ID, 'video-title').get_attribute('href'),
            channel=video.find_element(
                    By.XPATH, './/*[@id="text"]/a').get_attribute('innerHTML'),
            channel_link=video.find_element(
                    By.XPATH, './/*[@id="text"]/a').get_attribute('href')
        )

    def __get_data_from_comment(self, comment: object, position: int) -> dict:
        """Извлекает данные из переданного блока комментария

        Args:
            comment ([object]): Объект комментария
            position ([int]): Позиция выдачи на странице

        Returns:
            dict: Словарь с полученными данными по комментарию
        """
        return dict(
            comment_position=position+1,
            commentator_name=comment.find_element(
                By.XPATH, './/a[@id="author-text"]/span'
            ).text,
            comment_text=comment.find_element(By.ID, 'content-text').text,
            comment_likes=comment.find_element(By.ID, 'vote-count-middle').text
        )

    def get_common_data(self, query: str, depth: int = 50) -> list:
        """
        Метод для извлечения данных из поисковой выдачи YouTube по поисковому
        запросу.

        Args:
            query (str): Поисковый запрос
            depth (int, optional): Глубина извлечения данных из посковой выдачи.
            Defaults to 50.

        Raises:
            ValueError: Вызывается в случае если передана пустая
            строка в качестве входного параметра

        Returns:
            list: Возвращает список объектов в виде следующей структуры данных:
            {
                'position': int, # Позиция в выдаче
                'title': 'Some text', # Заголовок видео
                'query': 'query string', # Поисковый запрос
                'description': 'Video description text', #Текст с описанием видео
                'link': str, # Ссылка на видео
                'video_length': time, # Продолжительность видео
                'channel': str, # Назвиние канала
                'channel_link': str # Ссылка на канал
            }
        """
        if self.__check_query() is False:
            raise ValueError('Недопустимый запрос')

        for trying in range(3):
            try:
                self.__browser_instance.get(self.__url)
                # Ищем поле поиска на настранице
                search_field = WebDriverWait(self.__browser_instance, 5).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    '//input[@id="search"]'))
                )

                # Вставляем поисковый запрос в поле поиска и жмем Enter
                search_field.send_keys(Keys.CONTROL + "a")
                search_field.send_keys(Keys.DELETE)
                self.__browser_instance.implicitly_wait(1)
                search_field.send_keys(query)
                search_field.send_keys(Keys.ENTER)
                time.sleep(1)
                # Загрузим нужное количество видео на страницу
                while True:
                    videos = tuple(WebDriverWait(self.__browser_instance, 3).until(
                        EC.presence_of_all_elements_located(
                            (By.TAG_NAME, 'ytd-video-renderer'))
                    ))
                    self.__browser_instance.execute_script(
                        "window.scrollTo(0, document.documentElement.scrollHeight);")
                    time.sleep(1)
                    if len(videos) >= depth:
                        break
                # извлечем нужные данные из объектов videos
                common_data = []
                for video in videos:
                    common_data.append(
                        self.__get_common_data_from_video(
                            video,
                            query,
                            videos.index(video)
                        )
                    )
                del videos, video, search_field
                return common_data

            except Exception as err:
                print(f'Попытка {trying+1} закончилась неудачей. \n \
                        Ошибка: {err}')
                continue
        return None

    def get_overall_data(self, query: str,
                         depth: int = 50,
                         depth_comments: int = 100) -> list:
        """Полный проход по ключевому запросу с выводом более полной информации

        Args:
            query (str): Поисковый запрос
            depth (int, optional): Глубина просмотра поисковой
            выдачи. Defaults to 50.
            depth_comments (int, optional): Глубина просмотра комментариев
            под видео. Defaults to 100.

        Raises:
            ValueError: Возвращает в случае недопустимого запроса.

        Returns:
            list: Возвращает данные по видео с комментариями по поисковому 
            запросу
        """
        # Проверяем корректность запроса
        if self.__check_query() is False:
            raise ValueError('Недопустимый запрос')
        # Делаем 3 попытки сбора данных
        for trying in range(3):
            try:
                print(f"{trying+1} попытка - запрос: {query} \t \
                Глубина: {depth}")
                # Запускаем простой сбор данных по поисковому запросу
                common_data = self.get_common_data(query, depth)
                if common_data is None:
                    raise ValueError("Работа не завершена корректно")
                overall_data = []
                for item in common_data:
                    # Переходим по ссылке на видео
                    self.__browser_instance.get(item['link'])
                    # Отлавливаем ситуацию если комментариев меньше требуемого количества
                    comments_count = WebDriverWait(
                        self.__browser_instance, 8
                    ).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                '//h2[@id="count"]/yt-formatted-string/span'
                            )
                        )
                    )
                    comments_count = int(comments_count.text.replace(",", ""))
                    if depth_comments > comments_count:
                        depth_comments = comments_count
                    # Прокручиваем страницу вниз до загрузки нужного количества комментариев к видео
                    time.sleep(2)
                    while True:
                        comments = tuple(WebDriverWait(
                            self.__browser_instance, 3
                        ).until(
                            EC.presence_of_all_elements_located(
                                (By.ID, 'comment'))
                        ))
                        self.__browser_instance.execute_script(
                            "window.scrollTo(0, document.documentElement.scrollHeight);"
                        )
                        time.sleep(1)
                        if len(comments) >= depth_comments+2:
                            break

                    # Получаем все комментарии под видео
                    comments_data = []
                    comments = comments[0:depth_comments]
                    for comment in comments:
                        comments_data.append(
                            self.__get_data_from_comment(
                                comment,
                                comments.index(comment)))
                    # Извлекаем лайки и дизлайки
                    top_level_buttons = self.__browser_instance.find_element(
                        By.XPATH, './/div[@id="top-level-buttons"]'
                    )
                    likes_count = top_level_buttons.find_elements(
                        By.XPATH, './/ytd-toggle-button-renderer/ \
                        a/yt-formatted-string')[0].get_attribute('aria-label')
                    dislikes_count = top_level_buttons.find_elements(
                        By.XPATH, './/ytd-toggle-button-renderer/ \
                        a/yt-formatted-string')[1].get_attribute('aria-label')
                    # Добавляем данные в общий список данных
                    overall_data.append(dict(
                        position=item['position'],
                        title=item['title'],
                        query=item['query'],
                        description=self.__browser_instance.find_element(
                            By.ID, 'description').text,
                        link=item['link'],
                        views=self.__browser_instance.find_element(
                            By.XPATH, './/div[@id="count"]/yt-view-count-renderer/span').text,
                        release_date=self.__browser_instance.find_element(
                            By.ID, 'date').text,
                        channel=item['channel'],
                        channel_link=item['channel_link'],
                        likes_count=likes_count,
                        dislikes_count=dislikes_count,
                        comments_count=comments_count,
                        comments=comments_data
                    ))
                # Возвращаем полный список данных по поисковой выдачи
                return overall_data
            except Exception as err:
                print(f'Попытка {trying+1} закончилась неудачей. \n \
                        Ошибка: {err}')
                continue
        return None

    def __check_query(query: str) -> bool:
        if query is None or query == '':
            return False
        return True

    def __get_driver_path(self) -> str:
        """
        "Защищенный" метод определяет текущую операционную систему,
        возвращает путь к вебрайверу в зависимости от операционной системы.

        Raises:
            ValueError: Вызывается в случае неподходящей операционной системы.

        Returns:
            str: Возвращает строку с путем к необходимому вебдрайверу.
        """
        if platform == 'linux' or platform == 'linux2':
            # linux
            return os.path.dirname(
                os.path.abspath(__file__)) + \
                '\\drivers\\linux\\geckodriver'

        elif platform == 'darwin' or \
                platform == 'darwin2' or \
                platform == 'os2' or \
                platform == 'os2emx':
            # os x
            return os.path.dirname(
                os.path.abspath(__file__))+'\\drivers\\mac\\geckodriver'

        elif platform == 'win32' or platform == 'cygwin':
            # windows
            return os.path.dirname(
                os.path.abspath(__file__)) + \
                '\\drivers\\windows\\geckodriver.exe'

        else:
            raise ValueError('Ваша платформа не поддерживается.')

    def __create_browser_instance(self) -> object:
        """
        Метод создает объект вебдрайвера и возвращает его запущеный экземпляр
        готовый к дальнейшей работе.

        Raises:
            webdriver.WebDriverException: Выбрасывается исключение при создании
            и открытии вебдрайвера.

        Returns:
            object: возвращает объект вебдрайвера.
        """
        try:
            browser_instance = webdriver.Firefox(
                executable_path=self.__driver_path
            )
            return browser_instance
        except Exception as err:
            raise webdriver.WebDriverException(
                f'Возникла ошибка при создании вебдрайвера: {err}'
            )
