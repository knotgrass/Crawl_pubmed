# /home/agent/anaconda3/bin/python3.9
import os

from bs4.element import Tag
from colorama import Fore

from lib.utils import read_pmid, send_request

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


def split_info(info_one_paper: str) -> list:
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


def get_from_format_pubmed(body: Tag) -> list[list]:
    """
    Lấy thông tin PMID, title, abstract từ respond có query &format=pubmed
    Tạm thời áp dụng cho 

    ví dụ: https://pubmed.ncbi.nlm.nih.gov/?linkname=pubmed_pubmed_citedin&from_uid=32745377&show_snippets=off&format=pubmed&size=200
    trending, reference, cited by
    return list gồm các paper, mỗi paper 
    """
    if body is None:
        return None
    text = body.get_text(strip=True).strip()
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
                pmid = info[6:].strip()  # ; print(r"PMID- ", pmid)
                tong += 1

            elif info.startswith(r"TI  - ") and title == '':
                title = info[6:].strip()  # ; print(r"TI  - ", title)
                tong += 1

            elif info.startswith(r"AB  - ") and abstract == '':
                abstract = info[6:].strip()  # ; print(r"AB  - ", abstract)
                tong += 1

            if tong == 3:
                break
            # elif tong > 3:
            #     msg = r"Nhiều hơn 3 trường thông tin, kiểm tra lại các trường tt trong paper"
            #     raise Exception(msg)
        list_info_paper.append([pmid, title, abstract])

    return list_info_paper


def get_pmid_F1similar(path:str) -> list:
    """
    đọc thông tin trong file data/similarF1_Feb1.txt
    lấy ra danh sách pmid đã tìm thấy
    trong lúc crawls nếu gặp lại pmid này thì bỏ qua
    """
    path_list_pmid_similar = "data/similarF1_Feb1.txt"
    if not os.path.isfile(path):
        print("ko tìm thấy file")
        return []
    with open(path_list_pmid_similar, 'r', encoding= 'utf-8') as f:
        lines = f.read().strip().split('\n')

    return [l.strip() for i, l in enumerate(lines) if i % 4 == 0]


def get_info_similar_paper():
    """
    tìm info các similar paper với 4k paper đã biết trước
    """
    from lib.one_paper import find_similar_body
    from lib.utils import pmid2Url, read_pmid

    path_pmided = r"data/pmids_da_tim_similar.txt"
    path_pmid = r"data/pmids.txt"
    path_save_similar = r'data/similarF1_Feb1.txt'
    list_pmid = read_pmid(path_pmid)        # list pmid đã được xác định là liên quan đến bệnh di truyền
    list_pmided = read_pmid(path_pmided)    # list pmid đã crawls
    list_F1_pmid_similar = get_pmid_F1similar(path_save_similar)     # list pmid mới tìm được


    for pmid in list_pmid:      # 4k pmid
        if pmid in list_pmided: # empty
            continue    
        print("PMID is searching similar    ", pmid)    #BUG 31486992   10534763    23409989

        # lưu lại pmid đã tìm similar
        with open(path_pmided, 'a') as f:
            f.write(pmid + '\n')

        full_url = pmid2Url(pmid)
        body = send_request(full_url)
        similar = find_similar_body(body)

        # if similar is not None:
        list_paper = get_from_format_pubmed(similar)
        if list_paper is None: continue

        all_papers_info = ''
        for paper in list_paper:
            # chỉ lấy thông tin về các pmid mới tìm đc, check trùng xem đã tồn tại ở f0 và f1
            if paper[0] not in list_pmid and paper[0] not in list_F1_pmid_similar:
                all_papers_info += '\n'.join(paper) + '\n\n'
                list_F1_pmid_similar.append(paper[0])

        # viết thông tin tìm đc ra file pmid, title, abstract
        with open(path_save_similar, 'a', encoding= 'utf-8') as f1:
            f1.write(all_papers_info)
        
        # break


def get_200Trending_paper():
    # get paper trending
    path_trending = "data/en_trending_pubmed.txt"     # file để save thông tin paper trending
    url = r"https://pubmed.ncbi.nlm.nih.gov/?linkname=pubmed_pubmed_citedin&from_uid=32745377&show_snippets=off&format=pubmed&size=200"

    body = send_request(url)
    list_info_paper = get_from_format_pubmed(body)

    # get pmid positive and similar
    pmid_positive = get_pmid_F1similar() + read_pmid("data/pmids.txt")

    for paper in list_info_paper:
        if paper[0] not in pmid_positive:
            with open(path_trending, 'a', encoding= 'utf-8') as f:
                f.write('\n'.join(paper) + '\n\n')


if __name__ == "__main__":
    # get_200Trending_paper()
    get_info_similar_paper()
