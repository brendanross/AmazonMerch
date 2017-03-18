from amazonproduct import API
import bottlenose
import string
import requests
import ast 
from bs4 import BeautifulSoup
import time
from operator import itemgetter


api = API(locale='us')
alphabet = string.ascii_lowercase

amazon = bottlenose.Amazon("AKIAI6I6S4DKA32FXPNA",
                            "W8UyVeAUu1GPng0Ey8BkogcOq2A7AKn2cYXBD4qz",
                            "techtoysandtr-20",
                            Region = "US",
                            Parser=lambda text: BeautifulSoup(text, 'xml'),
                            MaxQPS=0.99
                        )


def keyword_finder():
    term = raw_input("Choose a Search Term: ")
    related_terms = []
    #Find related terms by appending A-Z to the search term.
    for letter in string.ascii_lowercase:
        r = requests.get("http://completion.amazon.com/search/complete?search-alias=fashion&client=amazon-search-ui&mkt=1&q={0}%20{1}".format(term, letter))
        word_list = ast.literal_eval(r.text)
        if len(word_list[1]):
            related_terms.extend(word_list[1])
        #time.sleep(0.75)
    i = 1
    for term in related_terms:
        print("{0}. {1}".format(i, term))
        i+=1
    term_number = raw_input("Check competition for term? Enter term number or Enter to return to main menu: ")
    if not term_number:
        main_menu()
    else:
        print related_terms[int(term_number)-1]
        check_competition(related_terms[int(term_number)-1])

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def get_rank_image(ASIN):
    rank_list = []
    image_list = []
    for x in batch(ASIN, 10):
        results = amazon.ItemLookup(ItemId=str(",".join(x)), ResponseGroup="SalesRank, Images")
        
        for item in results.find_all('Item'):
            rank = item.find('SalesRank')
            image = results.find('MediumImage').find('URL')
            if rank is None:
                rank_list.append('None')
            else:
                rank_list.append(int(rank.text))
            image_list.append(image.text)
    return rank_list, image_list

def get_price(ASIN):
    price_list = []
    for x in batch(ASIN, 10):
        results = amazon.ItemLookup(ItemId=str(",".join(x)), ResponseGroup="OfferSummary")
        price_list.extend(results.find_all('Amount'))       
    
    price_list = [price.text for price in price_list]
    return price_list

def get_results_keyword(term):
    #Define starting page.
    page = 1
    parent_asin_list = []
    child_asin_list = []
    print '{0} "Lightweight, Classic fit, Double-needle sleeve and bottom hem"'.format(term)
    items = amazon.ItemSearch(
                        Keywords='{0} "Lightweight, Classic fit, Double-needle sleeve and bottom hem"'.format(term),
                        SearchIndex="Fashion",
                        ItemPage = str(page),
                        )
    #TOTAL RESULTS CAN BE FOUND HERE! USE prettify() to find it.
    if items.find('TotalResults') is None:
        print("No results found for: {0}".format(term))
        
    for item in items.find_all('Item'):
        parent_asin = item.find('ParentASIN')
        child_asin = item.find('ASIN')
        if parent_asin is None:
            parent_asin_list.append(child_asin)
        else:
            parent_asin_list.append(parent_asin)
        child_asin_list.append(child_asin)

    #Loop through up to 10 pages.
    while ((len(parent_asin_list)%10) == 0) and (page < 10) and (len(parent_asin_list) != 0):
        page += 1
        print(page)
        items = amazon.ItemSearch(
                        Keywords='{0} "Lightweight, Classic fit, Double-needle sleeve and bottom hem"'.format(term),
                        SearchIndex="Fashion",
                        ItemPage = str(page)
                        )
        for item in items.find_all('Item'):
            parent_asin = item.find('ParentASIN')
            child_asin = item.find('ASIN')
            if parent_asin is None:
                parent_asin_list.append(child_asin)
            else:
                parent_asin_list.append(parent_asin)
            child_asin_list.append(child_asin)
        
        
        #parents = items.find_all('ParentASIN')
        #print len(parent_asin_list)
        #parent_asin_list.extend(parents)
        #child_asin_list.extend(items.find_all('ASIN'))
        #print parent_asin_list
    
    child_asin_list = [asin.text for asin in child_asin_list]
    parent_asin_list = [asin.text for asin in parent_asin_list]
    
    return parent_asin_list, child_asin_list

def get_results_merchant(merchant):
    #Define starting page.
    page = 1
    items = amazon.ItemSearch(
                        Keywords ='"Lightweight, Classic fit, Double-needle sleeve and bottom hem"',
                        Brand = merchant,
                        SearchIndex="Fashion",
                        ItemPage = str(page),
                        )
    #TOTAL RESULTS CAN BE FOUND HERE! USE prettify() to find it.
    
    #Find Parent and Child ASINs.
    parent_asin_list = items.find_all('ParentASIN')
    child_asin_list = items.find_all('ASIN')
 
    #Loop through up to 10 pages.
    while ((len(parent_asin_list)%10) == 0) and (page < 10) and (len(parent_asin_list) != 0):
        page += 1
        print(page)
        items = amazon.ItemSearch(
                        Keywords ='"Lightweight, Classic fit, Double-needle sleeve and bottom hem"',
                        Brand = merchant,
                        SearchIndex="Fashion",
                        ItemPage = str(page),
                        )
        parent_asin_list.extend(items.find_all('ParentASIN'))
        child_asin_list.extend(items.find_all('ASIN'))
    
    child_asin_list = [asin.text for asin in child_asin_list]
    parent_asin_list = [asin.text for asin in parent_asin_list]
    
    return parent_asin_list, child_asin_list
 
def check_merchant(merchant=None):
    if not merchant:
        merchant = raw_input("Enter Merchant name to check listings: ")
    #Create empty item list. Format: [[parent_asin], [child_asin], [price], [sales_rank], [image_url]]
    item_list = [i for i in range(5)]
    #Get Item Parent/Child ASIN
    item_list[0], item_list[1] = get_results_merchant(merchant)
    #Get Item Price
    item_list[2] = get_price(item_list[1])
    #Get SalesRank and ImageURL
    item_list[3], item_list[4] = get_rank_image(item_list[0])
    #print item_list[0]

def check_competition(term=None):
    if not term:
        term = raw_input("Enter term to check competition: ")
    
    #Get Item Parent/Child ASIN
    parent_asin_list, child_asin_list = get_results_keyword(term)
    #Get Item Price
    price_list = get_price(child_asin_list)
    #Get SalesRank and ImageURL
    sales_rank_list, image_url_list = get_rank_image(parent_asin_list)
    zipped_list = zip(sales_rank_list, parent_asin_list, child_asin_list, price_list, image_url_list)
    zipped_list.sort(key=itemgetter(0))
    print zipped_list
    #print zipped_list 
    #print len(item_list[2])
    # print len(item_list[3])
    # print len(item_list[4])
   
def main_menu():
    print("""
          1.Keyword Finder
          2.Check Competition
          3.Merchant Search
          """)
    choice = raw_input("Select an Option: ")
    if  choice == "1":
        keyword_finder()
    elif choice == "2":
        check_competition()
    elif choice == "3":
        check_merchant()

if __name__ == '__main__':
    main_menu()