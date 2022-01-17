# /home/agent/anaconda3/bin/python3.9
# from colorama import Fore
import os

from bs4.element import Tag

from lib import send_request

r"""
    Từ response của request có query &format=pubmed
    #    r"https://pubmed.ncbi.nlm.nih.gov/trending/?format=pubmed&size=200"
    #   "https://pubmed.ncbi.nlm.nih.gov/?show_snippets=off&format=pubmed&size=200&linkname=pubmed_pubmed_citedin&from_uid=32745377"


    phân tích html để lấy thông tin về 200 paper

    Chia nhỏ thành từng phần 1, mỗi phần là 1 paper
    Từ đó lấy ra 3 trường thông tin
    PMID : cho download full text
    title: classify
    abstract: classify
"""


def split_info(info_one_paper: str):
    r"""
         ____________________________________________________
        |.==================================================,|
        ||  Chia nhỏ thông tin trên 1 paper thành các dòng  ||
        ||  if char đầu dòng là khoảng trắng:               ||
        ||      ghép dòng đó vào dòng phía trên nó.         ||
        ||  else:                                           ||
        ||      Tạo dòng mới.                               ||
        ||  Ghép các trường thông tin lại với nhau.         ||
        ||  Tìm trường thông tin theo 7 char đầu tiên       ||
        ||     .~~~~.                                       ||
        ||   / ><    \  //                                  ||
        ||  |        |/\                                    ||
        ||   \______//\/                                    ||
        ||   _(____)/ /                                     ||
        ||__/ ,_ _  _/______________________________________||
        '===\___\_) |========================================'
             |______|
             |  ||  |
             |__||__|
             (__)(__)
    """

    lines = info_one_paper.strip().split('\n')
    list_info = []      # list chứa các trường thông tin
    info = [lines[0]]   # thông tin của 1 trường, ví dụ PMID- 35025605
    for line in lines[1:]:
        if line[0] == ' ':
            info.append(line.strip())
        else:
            list_info.append(' '.join(info))
            info.clear()
            info.append(line.strip())
    list_info.append(' '.join(info))

    return list_info


def get_from_format_pubmed(body: Tag) -> list:
    """
    Lấy thông tin PMID, title, abstract từ respond có query &format=pubmed
    Tạm thời áp dụng cho 

    ví dụ: https://pubmed.ncbi.nlm.nih.gov/?linkname=pubmed_pubmed_citedin&from_uid=32745377&show_snippets=off&format=pubmed&size=200
    trending, reference, cited by
    """
    text = body.get_text().strip()
    papers = text.split('\nPMID- ')

    list_info_paper = []
    for paper in papers:

        # Do split('\nPMID- ') nên từ paper thứ 2 trở đi bị mất string "\nPMID- "
        # Cần check và bổ sung thêm
        if not paper.startswith(r"PMID- "):
            paper = r"PMID- " + paper

        list_info = split_info(paper)

        tong: int = 0
        pmid = ''
        title = ''
        abstract = ''

        for info in list_info:
            if info.startswith(r"PMID- ") and pmid == '':
                pmid = info[6:]  # ; print(r"PMID- ", pmid)
                tong += 1

            elif info.startswith(r"TI  - ") and title == '':
                title = info[6:]  # ; print(r"TI  - ", title)
                tong += 1

            elif info.startswith(r"AB  - ") and abstract == '':
                abstract = info[6:]  # ; print(r"AB  - ", abstract)
                tong += 1

            if tong == 3:
                break
            # elif tong > 3:
            #     msg = r"Nhiều hơn 3 trường thông tin, kiểm tra lại các trường tt trong paper"
            #     raise Exception(msg)
        list_info_paper.append([pmid, title, abstract])

    return list_info_paper


if __name__ == "__main__":
    url = r"https://pubmed.ncbi.nlm.nih.gov/?show_snippets=off&format=pubmed&size=200&linkname=pubmed_pubmed&from_uid=31962139"
    body = send_request(url)
    papers = get_from_format_pubmed(body)
    for paper in papers:
        # paper[0] là pmid:str
        with open(os.path.join('data/paper', paper[0] + ".txt"), 'w') as f:
            f.write('\n'.join(paper))