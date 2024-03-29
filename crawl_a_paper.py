# /home/agent/anaconda3/bin/python3.9
from urllib.parse import urljoin

from bs4.element import Tag
from colorama import Fore  # , Back, Style

from lib.config import PUBMED
from lib.utils import add_query, pmid2Url, send_request


def find_title(body: Tag) -> str:
    # get title of paper
    title = body.find(name='h1', attrs={"class": "heading-title"})
    title =  title.get_text(strip= True).strip()
    return ' '.join(title.split())


def find_abstract(body: Tag) -> str:
    # get abstrack of paper
    absTag = body.find(name='div', attrs={"class": "abstract"}, recursive=True)
    if absTag is None:
        # tìm sai keywork trong tag html
        # nên ko tìm đc Tag chứa abstract
        raise Exception("check tag html và key:value trong tìm kiếm")
    else:
        _abstract = absTag.find('p')
        if _abstract is None:
            # NOTE format của đoạn html ko chứa abstract
            r"""
            <div class="abstract">
                <em class="empty-abstract">No abstract available</em>
            </div>
            """
            # trường hợp paper ko có abstract
            msg = absTag.find(
                'em', {"class": "empty-abstract"}, recursive=True)
            print(msg.get_text().strip())
            abstract = ""
        else:
            # NOTE format của đoạn html có chứa abstract
            r"""
            <div class="abstract" id="abstract">
                <h2 class="title">Abstract</h2>
                <div class="abstract-content selected" id="enc-abstract">
                    <p>
                        This article summarizes what is currently known about the 2019 novel
                        coronavirus and offers interim guidance.
                    </p>
                </div>
            </div>
            """
            # trường hợp paper có abstract
            abstract = _abstract.get_text().strip()
            abstract = ' '.join(abstract.split()) # loại bỏ các dấu xuống dòng, nhiều space về 1 space
    return abstract


def find_reference_body(body: Tag) -> Tag:
    r"""
        >>> input body html của HOMEPAGE/pmid
        >>> return body của page chứa full references paper

        format tag html cần tìm
                  <button
                aria-controls="top-references-list-1"
                class="show-all"
                data-ga-action="show_more"
                data-ga-category="reference"
                data-next-page-url="/32264957/references/"
                ref="linksrc=show_all_references_link"
              >
                Show all 19 references
              </button>
    """

    show_all_ref = body.find('button', {"aria-controls": "top-references-list-1",
                                        "class": "show-all", "data-ga-action": "show_more",
                                        "data-ga-category": "reference"}, recursive=True)

    if show_all_ref is None:
        return None  # nếu ko tìm thấy tag, return None
    
    nextPageUrl = show_all_ref.__getitem__(key="data-next-page-url")    # "/32264957/references/"

    # ref paper KO theo format nên ko dùng func add_query
    full_ref_url = urljoin(PUBMED, nextPageUrl)
    ref_body = send_request(full_ref_url)


    # <ol class="references-list" id="full-references-list-1">
    # ol = ref_body.find('ol', {"class":"references-list"}, recursive= True)

    return ref_body


def find_similar_body(body: Tag)->Tag:
    """
        5 url to 5 similar articals and 1 to search 1901 similar articals
    """
    see_allSimilarTag = body.find('a', {"class": "usa-button show-all-linked-articles", 
                                             "data-ga-action": "show_all", 
                                             "data-ga-category": "similar_article"}, recursive=True)
    if see_allSimilarTag is None:
        return None
    queryStr = see_allSimilarTag.__getitem__(key="data-href")   #"/?linkname=pubmed_pubmed&amp;from_uid=32264957"
    full_Similar_url = add_query(queryStr)
    body = send_request(full_Similar_url)

    return body


def find_cited_body(body: Tag)->Tag:
    r"""
    input: body của paper
    return : body của pape, gồm full cited
            body này đã có info pmid, title, abstract của nhiều paper
            đưa tiếp qua crawl_trending.split_info để lấy thông tin của từng paper

    format của tag html:
            <a
                class="usa-button show-all-linked-articles"
                data-href="/?linkname=pubmed_pubmed_citedin&amp;from_uid=32264957"
                data-ga-category="cited_by"
                data-ga-action="show_all"
            >
                See all "Cited by" articles
            </a>
    """
    show_all_cited = body.find('a', {"class": "usa-button show-all-linked-articles",
                               "data-ga-category": "cited_by", "data-ga-action": "show_all"}, recursive=True)

    # get query string dẫn đến full cited page of paper
    queryStr = show_all_cited.__getitem__(key="data-href")
    full_cited_url = add_query(queryStr)
    cited_body = send_request(full_cited_url)

    return cited_body


if __name__ == "__main__":
    url = r'https://pubmed.ncbi.nlm.nih.gov/32264957/'
    body = send_request(url=url)

    ref_body = find_reference_body(body)
    _ol = ref_body.find('ol', {"class":"references-list"}, recursive= True)

    # <li class="skip-numbering" value="1">
    list_li = _ol.find_all('li', {"class":"skip-numbering", "value":"1"}, recursive= True)

    li = list_li[1]   # test thử với 1 phẩn tử

    r"""
            <li class="skip-numbering" value="1">
        Wu F, Zhao S, Yu B, Chen YM, Wang W, Song ZG, et al. A new coronavirus
        associated with human respiratory disease in China. Nature.
        2020;579:265–269. doi: 10.1038/s41586-020-2008-3. -
        <a
            class="reference-link"
            data-ga-action="10.1038/s41586-020-2008-3"
            data-ga-category="reference"
            href="https://doi.org/10.1038/s41586-020-2008-3"
            ref="linksrc=references_link&amp;ordinalpos=1"
        >
            DOI
        </a>

        -
        <a
            class="reference-link"
            data-ga-action="PMC7094943"
            data-ga-category="reference"
            href="http://www.ncbi.nlm.nih.gov/pmc/articles/pmc7094943/"
            ref="linksrc=references_link&amp;ordinalpos=2"
        >
            PMC
        </a>

        -
        <a
            class="reference-link"
            data-ga-action="32015508"
            data-ga-category="reference"
            href="/32015508/"
            ref="linksrc=references_link&amp;ordinalpos=3"
        >
            PubMed
        </a>
    </li>
    """
    # XXX DOI
    doi_Tag = li.find('a', {"ref":"linksrc=references_link&amp;ordinalpos=1"}, recursive= True)
    doi_text = doi_Tag.get_text(strip=True).strip() # DOI
    doi_url = doi_Tag.__getitem__(key="href")   # https://doi.org/10.1038/s41586-020-2008-3

    # XXX PMC
    pmc_Tag = li.find('a', {"ref":"linksrc=references_link&amp;ordinalpos=2"}, recursive= True)
    pmc_text = pmc_Tag.get_text(strip=True).strip()
    pmc_url = pmc_Tag.__getitem__(key="href")   # http://www.ncbi.nlm.nih.gov/pmc/articles/pmc7110798/

    # XXX PubMed
    pubmed_Tag = li.find('a', {"ref":"linksrc=references_link&amp;ordinalpos=3"}, recursive= True)
    pubmed_text = pubmed_Tag.get_text(strip=True).strip()
    pubmed_url = pubmed_Tag.__getitem__(key="href")
    pubmed_url = pmid2Url(pubmed_url)

    allString = [s for s in li._all_strings(strip=True, types=li.default)]  #self.get_text()
    



    print(Fore.RED + li.get_text(separator="", strip=True))
