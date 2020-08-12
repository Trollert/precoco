import pickle
import re
import os
from lxml import etree, html
from lxml.html.clean import Cleaner
from textwrap import wrap as text_wrap
from tkinter import messagebox

import precoco.common.patterns as pt
import precoco.common.globalflags as gf
from precoco.common.miscfunctions import is_date, save_replacements


def get_false_numbers(tree, path):
    """
    This function parses the table numbers of tree and returns a list of numbers that didn't match
    the pattern regNumbers from patterns module
    If a pickle file is present in the report directory, the saved replacements are applied beforehand
    :param tree:
    :param path: path to report directory
    :return: list of false numbers
    """
    # check numbers in table cells
    # get all tables that are not footnote tables
    el_table_text_cells = tree.xpath('//table[not(@class="footnote")]//*[normalize-space(text())]')
    list_false_number_matches = []
    # if save numbers file exists, replace matches before finding new ones
    if os.path.exists(path + '/save_numbers.pkl'):
        save_file = open(path + '/save_numbers.pkl', 'rb')
        save_dict = pickle.load(save_file)
        save_file.close()
        for cell in el_table_text_cells:
            if cell.text is not None:
                for old, new in save_dict.items():
                    cell.text = cell.text.replace(old, new)

    for cell in el_table_text_cells:
        if cell.text is not None:
            if is_number(cell):
                remove_br_tag(cell)
            elif is_date(cell.text_content()):
                remove_br_tag(cell)
            elif is_date(cell.text_content(), ignore_whitespace=True):
                remove_br_tag(cell)
                cell.text = re.sub('\s', '', cell.text)
            elif any(reg.fullmatch(cell.text_content()) for reg in pt.regMisc + pt.regHeaderContent):
                continue
            # if no match could be found, try to fix it or move it to false match list
            else:
                if gf.b_fix_numbers.get():
                    # if cell only contains number tokens, try to fix format
                    if re.fullmatch(r'[0-9,. \-+]*', cell.text_content()):
                        # drop br-tag if one is found
                        remove_br_tag(cell)
                        # if, after removing whitespace, the resulting format matches a number format,
                        # remove the whitespace from tree element
                        if any(reg.fullmatch(re.sub(r'\s+', '', cell.text)) for reg in pt.regNumbers):
                            cell.text = re.sub(r'\s+', '', cell.text)
                        # if you cant fix it, append to false number list
                        else:
                            list_false_number_matches.append(cell.text)
                    # otherwise append it to false number match list
                    else:
                        list_false_number_matches.append(cell.text)
                else:
                    list_false_number_matches.append(cell.text)
    list_false_number_matches = list(dict.fromkeys(list_false_number_matches))
    return list_false_number_matches


def get_false_words(tree, path):
    """
    This function parses the text elements of tree and returns a list of words that didn't match
    the pattern regFalseWords from patterns module
    If a pickle file is present in the report directory, the saved replacements are applied beforehand
    :param tree:
    :param path: path to report directory
    :return: list of false words
    """
    # check false word separations
    # get all elements that contain text (p/h1/h2/h3/td)
    # global lAllFalseWordMatches
    list_all_matches = []
    el_all_text = tree.xpath('.//*[normalize-space(text())]')
    # check for saved replacements and apply them if found
    if os.path.exists(path + '/save_words.pkl'):
        save_file = open(path + '/save_words.pkl', 'rb')
        save_dict = pickle.load(save_file)
        save_file.close()
        for e in el_all_text:
            if e.text is not None:
                for old, new in save_dict.items():
                    e.text = e.text.replace(old, new)
                    # check tail as well
                    if len(e):
                        for t in e:
                            if t.tail:
                                t.tail = t.tail.replace(old, new)
    # regex match on every text element to check whether it matches a wrongfully separated word
    for e in el_all_text:
        if e.text is not None:
            # search the whole text for URLs and put them in a list
            # this is done via list comprehension because the regex.findall returns a list of tuples
            url_matches = [x[0] for x in pt.regURL.findall(e.text_content())]
            for regex_match in pt.regFalseWords:
                list_current_matches = regex_match.findall(e.text_content())
                # if matches were found
                if list_current_matches:
                    # print(list_current_matches)
                    list_current_matches = [elem for elem in list_current_matches if elem not in pt.lAllowedWords]
                    # compare them to eventually found urls in the current element
                    if url_matches:
                        # don't add them to the new list if they're a part of a URL
                        list_current_matches = [elem for elem in list_current_matches if any(elem not in url for url in url_matches)]
                    list_all_matches.extend(list_current_matches)
    list_false_word_matches = list(dict.fromkeys(list_all_matches))
    return list_false_word_matches


def replace_number_list(tree, list_new, list_old, report_path):
    """
    parses the table numbers and replaces fixed numbers from list_new
    saves replacements in pickle file
    :param tree:
    :param list_new: list of replacements
    :param list_old: list of wrong numbers
    :param report_path: path to report dir
    :return: tree
    """
    el_numbers_table = tree.xpath('//table[not(@class="footnote")]/tr/td[normalize-space(text())]')
    # get a list of listbox lines
    list_temp_new = list_new.copy()
    list_temp_old = list_old.copy()
    for i in reversed(range(len(list_temp_old))):
        if list_temp_old[i] == list_temp_new[i]:
            list_temp_old.pop(i)
            list_temp_new.pop(i)

    # create file to safe already replaced numbers in case of error
    save_replacements(dict(zip(list_temp_old, list_temp_new)), '/save_numbers.pkl', report_path)

    for e in el_numbers_table:
        for i in range(len(list_temp_new)):
            if e.text:
                e.text = e.text.replace(list_temp_old[i], list_temp_new[i])
    return tree


def replace_word_list(tree, list_new, list_old, report_path):
    """
    parses the text elements and replaces fixed words from list_new
    saves replacements in pickle file
    :param tree:
    :param list_new: list of replacements
    :param list_old: list of wrong numbers
    :param report_path: path to report dir
    :return: tree
    """
    el_text = tree.xpath('.//*[normalize-space(text())]')
    # get a list of listbox lines
    corrected_list = list(list_new).copy()

    # create duplicate to not create confusion while popping
    list_temp_old = list_old.copy()

    # remove unaffected entries from both lists
    for i in reversed(range(len(list_temp_old))):
        if list_temp_old[i] == corrected_list[i]:
            list_temp_old.pop(i)
            corrected_list.pop(i)

    # create file to safe already replaced words in case of error
    save_replacements(dict(zip(list_temp_old, corrected_list)), '/save_words.pkl', report_path)

    for e in el_text:
        for i in range(len(corrected_list)):
            if e.text:
                e.text = e.text.replace(list_temp_old[i], corrected_list[i])
            # check tail as well (if present)
            if len(e):
                for t in e:
                    if t.tail:
                        t.tail = t.tail.replace(list_temp_old[i], corrected_list[i])
    return tree


def remove_false_text_breaks(tree):
    """
    removes false text breaks in p-tags depending on capitalized letters
    :param tree:
    :return: tree
    """
    all_text_elements = tree.xpath('/html/body/p')
    for i in range(len(all_text_elements)):
        try:
            # check end and start char of two adjacent p-tag-strings
            pop_idx = []
            for j in range(1, len(all_text_elements)):
                if pt.reg_false_break_indicator_end.search(all_text_elements[i].text_content()) and \
                        pt.reg_false_break_indicator_start.search(all_text_elements[i+j].text_content()):
                    # add space if needed
                    if not all_text_elements[i].text_content().endswith(' '):
                        if gf.flag_is_formatted and all_text_elements[i + j][0].text:
                            all_text_elements[i + j][0].text = ' ' + all_text_elements[i + j][0].text
                        elif all_text_elements[i + j].text:
                            all_text_elements[i + j].text = ' ' + all_text_elements[i + j].text
                    # append second element to first
                    all_text_elements[i].append(all_text_elements[i+j])
                    # remove the tag from second element to prevent nested paragraphs
                    all_text_elements[i+j].drop_tag()
                    pop_idx.append(i+j)
                else:
                    for p in pop_idx:
                        all_text_elements.pop(p)
                    break
        except IndexError:
            # this exception is only raised when reaching the end of the list
            # so this is just ignored
            continue
    return tree


def analyze_style_tag(style_element, p_elements, accuracy=10):
    """
    this function takes the style element and analyzes the font sizes in p_elements
    it takes the different font names into consideration and returns a dict of font identifiers (e.g. font2)
    a lower accuracy means more false positives
    :param style_element:
    :param p_elements:
    :param accuracy: 0-100 lower returns more false positives
    :return: dict of heading candidates
    """
    # get list of raw style font text
    list_styles = [element for element in style_element[0].text.splitlines() if element.startswith(' .font')]
    # extract font sizes as integer list
    list_font_sizes = [int(re.findall(r'(?<=font:)\d+(?=pt)', size)[0]) for size in list_styles]
    # extract font name as string list
    list_font_names = [re.findall(r'(?<=pt )[\w\s]*?(?=,)', style)[0] for style in list_styles]
    # create list of font identifiers ('font0, font1, ...)
    list_font_identifiers = ['font' + str(i) for i in range(len(list_styles))]
    # create dict from identifiers and sizes
    font_sizes = dict(zip(list_font_identifiers, list_font_sizes))
    # create dict from identifiers and names
    font_names = dict(zip(list_font_identifiers, list_font_names))

    # create dict for occurrence count
    font_occurrences = dict(zip(list_font_identifiers, [0] * len(list_styles)))
    # count all the occurrences of the specific fonts
    for p in p_elements:
        font_occurrences[re.findall(r'font\d+', p.find('span').attrib['class'])[0]] += 1
    # get percentages of occurrences
    sum_occurrences = sum(font_occurrences.values())
    font_occurrence_percentage = dict(zip(list_font_identifiers, [k / sum_occurrences for k in font_occurrences.values()]))
    # pop zero element candidates from all lists
    poplist = []
    for key, value in font_occurrences.items():
        if value == 0:
            poplist.append(key)
    for key in poplist:
        font_occurrences.pop(key)
        font_sizes.pop(key)
        font_occurrence_percentage.pop(key)

    # mark all possible heading candidates
    max_key = max(font_occurrence_percentage, key=font_occurrence_percentage.get)
    max_value = font_occurrence_percentage[max_key]
    max_size = font_sizes[max_key]
    heading_candidates = {}
    for key, value in font_occurrence_percentage.items():
        if max_value > value + (accuracy / 100) and font_sizes[key] >= max_size + accuracy / 5:
            if font_names[key] == font_names[max_key]:
                heading_candidates[key] = 1
            elif font_sizes[key] > max_size + accuracy / 4:
                heading_candidates[key] = 1
    return heading_candidates


def set_span_headings(tree):
    """
    this function only gets called when a formatted htm-file is detected (export as "formatted text" from ABBYY)
    it analyzed the css style tags and changes text to h3 depending on font size
    :param tree:
    :return: tree
    """
    # merges multiple span tags into one, while retaining biggest font size
    for p in tree.xpath('/html/body/p[count(*)>1]/span[@style or @class]/parent::*'):
        span = p.findall('span')
        # get font class number of first element
        class_attrib = int(re.findall(r'(?<=font)\d+', span[0].attrib['class'])[0])
        # iterate over remaining span tags and replace font size if bigger
        for s in span[1:]:
            if hasattr(s, 'class'):
                fontsize = int(re.findall(r'(?<=font)\d+', s.attrib['class'])[0])
                if fontsize > class_attrib:
                    class_attrib = fontsize
            span[0].append(s)
            s.drop_tag()
        span[0].attrib['class'] = 'font' + str(class_attrib)

    # if specific style attribute are found, directly convert to header
    # select all span tags that are the only thing present in a p tag (heading candidates)
    for p in tree.xpath('/html/body/p[count(*)=1]/span[@style]/parent::*'):
        try:
            if p[0].attrib['style'] in ['font-weight:bold;', 'font-style:italic;', 'text-decoration:underline;']:
                if not p.xpath('./span[normalize-space(.)]')[0].text.endswith(('.', ':')):
                    p.tag = 'h3'
        except KeyError:
            pass

    # get style tag content of htm-file
    style_content = tree.xpath('/html/head/style')
    # get all p-tags that contain span tags
    el_spans = tree.xpath('body/p[count(*)=1]/span[@class]/parent::*')
    # returns a dict of font identifiers who are considered heading candidates
    heading_candidates = analyze_style_tag(style_content, el_spans, 10)
    # change text to heading based on heading_candidates
    for p in el_spans:
        if re.findall(r'font\d+', p[0].attrib['class'])[0] in heading_candidates \
                and not p[0].text.endswith(('.', ':')) \
                and not pt.regUnorderedList[0].match(p[0].text) \
                and not pt.regUnorderedList[0].match(p.getnext().text_content()):
            p.tag = 'h3'
    # remove trash br tags
    for br in tree.xpath('//br[@*]'):
        br.drop_tag()

    return tree


def merge_tables_vertically(tree):
    """
    the function merges marked tables vertically if the number of columns match up
    displays warnings if the user wants to merge tables with different amounts of columns
    :param tree:
    :return: tree
    """
    el_merge_tables = tree.xpath(
        '//table[tr[1]/td[1][starts-with(normalize-space(text()),"§§")] or tr[last()]/td[last()][starts-with(normalize-space(text()),"§§")]]')
    list_to_merge = []
    flag_continue_merge = False
    for table in el_merge_tables:
        iCols = []
        flag_start_marker = table.xpath('./tr[1]/td[1][starts-with(normalize-space(text()),"§§")]')
        flag_end_marker = table.xpath('./tr[last()]/td[last()][starts-with(normalize-space(text()),"§§")]')
        # check if table has end marker (§§)
        if flag_end_marker:
            # and start marker?
            if flag_start_marker:
                # is merge list empty?
                if not list_to_merge:
                    # BUG
                    add_to_error_log('Error in marker start or end position! Check the markers in ABBYY!\n'
                            'Error found in table with start marker: ' + str(table.xpath('./tr[1]/td[1]/text()')) + '\n'
                            'and end marker: '
                                     + str(table.xpath('./tr[last()]/td[last()]/text()')))
                    flag_continue_merge = False
                    gf.flag_found_error = True
                    continue
                else:
                    list_to_merge.append(table)
                    flag_continue_merge = True
            else:
                list_to_merge.append(table)
                flag_continue_merge = True
        elif flag_start_marker:
            if not list_to_merge:
                # BUG
                add_to_error_log('Error in start marker position! Check the markers in ABBYY!\n'
                      'Error found in table with start marker: ' + str(table.xpath('./tr[1]/td[1]/text()')))
                flag_continue_merge = False
                gf.flag_found_error = True
                continue
            else:
                list_to_merge.append(table)
                flag_continue_merge = False
        else:
            add_to_error_log('No markers detected, this shouldnt happen, report this bug!')
            gf.flag_found_error = True
            break
        # next table included in merge?
        # if not merge collected tables
        if not flag_continue_merge:
            # check if all tables in merge list have the same number of columns
            i_col_numbers = []
            index_tables = []
            for mTable in list_to_merge:
                i_col_numbers.append(get_max_columns(mTable))
                # get indices of tables to merge
                index_tables.append(tree.find('body').index(mTable))
            # do all merging candidates have the same number of columns?
            if len(set(i_col_numbers)) == 1:
                # before merging, check whether all the tables in this merging process are consecutive tables within
                # the body tag
                # if not only raise warning
                # TODO: raise warning and give user option to not proceed
                if index_tables != list(range(min(index_tables), max(index_tables)+1)):
                    add_to_error_log('You try to merge tables that are not consecutive within the html.\n'
                          'Please check the table set beginning with'
                          ' ' + str(list_to_merge[0].xpath('./tr[last()]/td[last()]/text()')) + ' as end marker, ' +
                                     str(len(list_to_merge)) + ' subtables and ' +
                                     str(i_col_numbers) + ' columns.\n\n'
                          'This is fairly unusual, but the merging process will still be executed.\n'
                          'Redo the processing after fixing in ABBYY or Sourcecode, if this was not intentional!')
                    gf.flag_found_error = True
                # remove end marker
                # for first table
                list_to_merge[0].xpath('./tr[last()]/td[last()]')[0].text = list_to_merge[0].xpath('./tr[last()]/td[last()]')[
                    0].text.replace('§§', '')
                for i in range(1, len(list_to_merge)):
                    # remove start markers
                    if list_to_merge[i].xpath('./tr[1]/td[1]')[0].text is not None:
                        list_to_merge[i].xpath('./tr[1]/td[1]')[0].text = list_to_merge[i].xpath('./tr[1]/td[1]')[
                            0].text.replace('§§', '')
                    # remove end markers
                    # and every other table
                    if list_to_merge[i].xpath('./tr[last()]/td[last()]')[0].text is not None:
                        list_to_merge[i].xpath('./tr[last()]/td[last()]')[0].text = \
                            list_to_merge[i].xpath('./tr[last()]/td[last()]')[0].text.replace('§§', '')
                    # append all rows from all tables to first table
                    for row in list_to_merge[i]:
                        list_to_merge[0].append(row)
                    # remove now empty table
                    list_to_merge[i].getparent().remove(list_to_merge[i])
            else:
                add_to_error_log(
                    'You try to merge tables with different amount of table columns. Fix this in ABBYY or CoCo! Tables will not be merged!')
                add_to_error_log('Table end marker: ' + str(list_to_merge[0].xpath('./tr[last()]/td[last()]/text()')))
                add_to_error_log('The number of columns within the subtables are: ' + str(i_col_numbers))
                gf.flag_found_error = True
            list_to_merge.clear()
    return tree


def split_rowspan(tree):
    """
    this function is very complex because of the nature of tables and cell-merging in html
    it iterates through the columns, therefor indices and range() is used, not the element-wise iteration
    it creates a matrix in which the offsets of all td-cells are documented depending on the colspans within the same
    row, including new colspans from rowspan cells
    :param tree:
    :return: tree
    """
    # get all tables that have at least one td-attribute of rowspan with a value greater than 1
    el_rowspan_tables = tree.xpath('//table[tr/td[@rowspan > 1]]')
    for table in el_rowspan_tables:
        # create 0-matrix of the raw table dimensions
        matrix_correction = [[0 for x in range(get_max_columns(table))] for y in range(len(table))]
        # list to remember already processed cells
        cell_history = []
        # iterate td
        for i in range(get_max_columns(table)):
            # iterate tr
            for j in range(len(table)):
                # select cell depending on indices and the offset given by matrix
                cell = table.xpath('./tr[' + str(j + 1) + ']/td[' + str(i + 1 + matrix_correction[j][i]) + ']')
                # if cell was already processed skip to next cell
                if cell in cell_history:
                    continue
                # if not append it to history
                cell_history.append(cell)
                # get number of colspan/rowspan if any are present in td tag
                nr_cs = cell[0].get('colspan')
                nr_rs = cell[0].get('rowspan')

                if nr_cs is not None and int(nr_cs) > 1:
                    # offset is set, beginning at current cell, starting with 0 and decreasing to negative colspan value + 1
                    for c in range(int(nr_cs)):
                        matrix_correction[j][i + c] += -c
                    # change the offset of the remaining cells to maximum negative offset given from colspan value + 1
                    matrix_correction[j][i + int(nr_cs):] = [a - int(nr_cs) + 1 for a in matrix_correction[j][i + int(nr_cs):]]
                # if cell has rowspan insert corresponding number of empty cells in the following rows
                if nr_rs is not None and int(nr_rs) > 1:
                    for nrRowspan in range(1, int(nr_rs)):
                        if nr_cs is not None and int(nr_cs) > 1:
                            table[j + nrRowspan].insert(i + matrix_correction[j + nrRowspan][i], etree.Element('td', attrib={'colspan': nr_cs}))
                        else:
                            table[j + nrRowspan].insert(i + matrix_correction[j + nrRowspan][i], etree.Element('td'))
                    # finally remove the rowspan attribute
                    del cell[0].attrib['rowspan']
    return tree


def remove_empty_rows(tree):
    """
    removes all empty rows in tables, even with colspan or header tags
    :param tree:
    :return: tree
    """
    # remove empty table rows
    for row in tree.xpath('//tr[* and not(*[node()])]'):
        row.getparent().remove(row)
    return tree


def set_unordered_list(tree):
    # find and set unordered lists
    list_dash_candidates = []
    i_dash_count = 0
    flag_end_block = False
    current_block_dash = ''
    index_indent = []
    for p in tree.xpath('//body/p'):
        # check if beginning of paragraph matches safe list denominators
        if p.text:
            # create match object,
            # None if nothing was matched
            # returns match when something was found
            object_match = pt.regUnorderedList[0].match(p.text)
            if object_match:
                # if this is the first element in this chunk define dash denominator
                if not i_dash_count:
                    current_block_dash = object_match.group(0)
                i_dash_count += 1
                # check if the next element in root is also p
                if p.getnext().tag == 'p':
                    # if current dash denominator is not equal to the first dash
                    # this might be a indented list element so append its index to list
                    if current_block_dash != object_match.group(0):
                        index_indent.append(i_dash_count - 1)
                    list_dash_candidates.append(p)
                # if only one dashed element was found, check if it ends with a dot and only append if it did
                elif i_dash_count == 1:
                    flag_end_block = True
                    if p.text.endswith('.'):
                        list_dash_candidates.append(p)
                # if next element is not of type p, check if current dash is of chunk type,
                # if not check whether it might be of an indented group
                elif current_block_dash != object_match.group(0):
                    flag_end_block = True
                    if object_match.group(0) == list_dash_candidates[-1].text[:2]:
                        list_dash_candidates.append(p)
                        index_indent.append(i_dash_count - 1)
                else:
                    flag_end_block = True
                    list_dash_candidates.append(p)
            # if dash elements were found, but its only one and it doesnt end with a dot, pop it from candidate list
            elif list_dash_candidates:
                flag_end_block = True
                if i_dash_count == 1 and not list_dash_candidates[0].text.endswith('.'):
                    list_dash_candidates.pop()
        # if flag_end_block is True, convert the current block to li
        if flag_end_block:
            flag_end_block = False
            # only execute if dash elements were found
            if list_dash_candidates:
                # select parent body-tag
                currentParent = list_dash_candidates[0].getparent()
                # insert outer ul-tag at the index of the first dash group element
                outerUl = etree.Element('ul')
                currentParent.insert(currentParent.index(list_dash_candidates[0]), outerUl)
                # change tag of all dash elements to li and insert into ul-tag
                for li in list_dash_candidates:
                    li.text = pt.regUnorderedList[0].sub('', li.text, count=1)
                    li.tag = 'li'
                    outerUl.append(li)
                # if indented elements were found, split index-list into sublists of consecutive chunks
                if index_indent and gf.b_indent_unordered_list.get():
                    # iterate in reverse order to not mess up already moved elements
                    for subList in reversed(split_non_consecutive(index_indent)):
                        # insert inner ul-tag at first sublist elements position
                        innerUl = etree.Element('ul')
                        outerUl.insert(subList[0], innerUl)
                        # finally move indented elements into the ul-tag
                        for elem in subList:
                            innerUl.append(list_dash_candidates[elem])
                list_dash_candidates.clear()
                index_indent.clear()
            i_dash_count = 0
    return tree


def set_footnote_tables(tree):
    """
    marks tables as footnotes depending on nr. of colums and content of the first column
    :param tree:
    :return: ree
    """
    el_tables = tree.xpath('//table')
    # check if tables are footnote tables
    for table in range(len(el_tables)):
        el_first_col_cells = []
        list_b_is_anchor = []
        # check first whether table is exactly 2 columns wide
        if len(el_tables[table].xpath('.//tr[last()]/td')) == 2:
            # create list from first column values
            el_first_col_cells.append(el_tables[table].xpath('.//tr/td[1]'))
            # flatten list
            el_first_col_cells = [item for sublist in el_first_col_cells for item in sublist]
            # check if any footnote regex pattern matches, if yes set corresponding matches list value to true
            for cell in el_first_col_cells:
                # remove sup, sub-tags if found
                for el in cell:
                    if el.tag == 'sup' or el.tag == 'sub':
                        el.drop_tag()
                # create list with bool values of every regex, td-value match
                if cell.text is not None:
                    list_b_is_anchor.append(any(list(reg.fullmatch(cell.text) for reg in pt.regFootnote)))
                else:
                    list_b_is_anchor.append(False)
            # check if all footnote cell values matched with regex pattern
            if all(list_b_is_anchor):
                # if yes set table attribute to "footnote" and insert anchors
                for cell in el_first_col_cells:
                    etree.SubElement(cell, 'a', id='a' + str(table + 1) + str(el_first_col_cells.index(cell)))
                el_tables[table].set('class', 'footnote')

            # clear lists
            el_first_col_cells.clear()
            list_b_is_anchor.clear()
    return tree


def set_headers(tree):
    """
    sets headers of non footnote tables depending on content declared by regHeaderContent
    :param tree:
    :return: tree
    """
    # set table headers row for row
    el_standard_tables = tree.xpath('//table[not(@class="footnote")]')
    for table in el_standard_tables:
        flag_is_header = False
        flag_break_out = False
        i_header_rows = -1  # -1 for later comparison with 0 index
        i_old_header_row = -1
        for row in table:
            for cell in row:
                if cell.text:
                    # first compare cell content to header content matches or date type
                    # if anything matches, set current row to header row
                    if any(list(reg.fullmatch(cell.text) for reg in pt.regHeaderContent)) or is_date(cell.text):
                        flag_is_header = True
                        i_header_rows = table.index(row)
                    # then compare to number matches
                    # if it matches here the function quits and reverts back to previous header row
                    if any(list(reg.fullmatch(cell.text) for reg in pt.regNumbers)):
                        i_header_rows = i_old_header_row
                        flag_break_out = True
                        break
            if flag_break_out:
                break
            i_old_header_row = i_header_rows

        # get the first occuring row in which the first cell is not empty
        el_first_non_empty_row = table.xpath('./tr[td[position() = 1 and text()]][1]')
        if len(el_first_non_empty_row):
            # index of the first cell with text - 1 to get only empty cells
            first_text_cell_row = table.index(el_first_non_empty_row[0]) - 1
            # compare to header content matches
            if i_header_rows <= first_text_cell_row:
                i_header_rows = first_text_cell_row
                flag_is_header = True
        # when no header is found and table is of specific size, set first row to header row
        if len(table) >= 4 and get_max_columns(table) >= 3 and i_header_rows == -1:
            i_header_rows = 0
            flag_is_header = True
        # if the whole table would be headers just set the first one to header
        if len(table) == i_header_rows + 1:
            i_header_rows = 0

        if flag_is_header:
            # create lists with header and body elements
            # this is needed at the beginning, because the position changes when adding header and body tags
            headers = table.xpath('.//tr[position() <= %s]' % str(i_header_rows + 1))
            body = table.xpath('.//tr[position() > %s]' % str(i_header_rows + 1))
            # create thead-/tbody-tags
            table.insert(0, etree.Element('tbody'))
            table.insert(0, etree.Element('thead'))

            # move rows to inside header or body
            for thead in headers:
                table.find('thead').append(thead)
            for tbody in body:
                table.find('tbody').append(tbody)
    return tree


def replace_custom_characters(tree):
    table_cells = tree.xpath('//table[not(@class="footnote")]//*[text()]')
    for cell in table_cells:
        if cell.text is not None:
            cell.text = re.sub(r' \)', ')', cell.text)
            cell.text = re.sub(r']', ']', cell.text)
            cell.text = re.sub(r'\[', '[', cell.text)
            cell.text = re.sub(r'Telefonica|Telefönica', 'Telefónica', cell.text)
        if len(cell):
            for c in cell:
                if c.tail is not None:
                    c.tail = re.sub(r' \)', ')', c.tail)
                    c.tail = re.sub(r']', ']', c.tail)
                    c.tail = re.sub(r'\[', '[', c.tail)
                    c.tail = re.sub(r'Telefonica|Telefönica', 'Telefónica', c.tail)
    return tree



def fix_tsd_separators(tree, dec_separator):
    """
    this function fixed falsly formatted numbers within tables which should be thousand-separated by a space and decimal
    separated by a chooseable separator "decSeparator"
    the precision of decimal places is adopted from each original number
    THIS FUNCTION SHOULD ONLY BE USED WITH FONDS REPORTS AND SPACE SEPARATED NUMBER FORMAT
    :param tree:
    :param dec_separator:
    :return: tree
    """
    # exclude header and leftmost column from reformatting
    for table in tree.xpath('//table[not(@class="footnote")]'):
        for cell in table.xpath('.//tbody/tr/td[position() > 1]'):
            if cell.text is not None:
                # only affect cells with numbers
                if re.fullmatch('-?\s?[\d\s,]+', cell.text):
                    # clean all whitespace from number
                    no_space = cell.text.replace(' ', '')
                    # find nr of decimal places
                    nr_dec_places = no_space[::-1].find(dec_separator)
                    # if none are found = -1 so fix that to 0
                    if nr_dec_places < 0 : nr_dec_places = 0
                    # reformat string to match float format
                    # reformat float to insert thousand separators and preserve the nr of decimal places
                    # replace tsd separators to chosen separator
                    cell.text = '{:,.{prec}f}'.format(float(no_space.replace(',', '.')), prec=nr_dec_places).replace(',', ' ').replace('.', dec_separator)
    return tree


def rename_pictures(tree, file_path):
    """
    this function changes .png images to .jpg and replaces the necessary parts in the tree elements
    :param tree:
    :param file_path:
    :return:
    """
    folder_pics = os.path.splitext(file_path)[0] + '_files'
    if os.path.exists(folder_pics):
        for filename in os.listdir(folder_pics):
            base_file, ext = os.path.splitext(filename)
            if ext == ".png":
                # rename reference in htm file
                # get 'img' tag
                e_png_pic = tree.xpath('//img[@src="' + os.path.basename(folder_pics) + '/' + filename + '"]')
                # rename attribute "src"
                e_png_pic[0].attrib['src'] = os.path.basename(folder_pics) + '/' + base_file + '.jpg'
                # rename picture file
                os.rename(folder_pics + '/' + filename, folder_pics + '/' + base_file + ".jpg")
    return tree


def break_fonds_table(tree):
    """
    this function inserts br-tags in the header and first column of the big "Vermögensaufstellung" Table in fonds reports
    it hereby wraps the cell text to a specific length, which is set to 14 characters while not breaking longer words
    THIS FUNCTION SHOULD ONLY BE USED WHEN A FONDS REPORT NEEDS TO BE BROKEN DOWN INTO CHUNKS
    :return: tree
    """
    e_fonds_table = tree.xpath(
        '/html/body/*[starts-with(normalize-space(text()),"Vermögensaufstellung")]/following-sibling::table[1]')
    for table in e_fonds_table:
        title_col_cells = table.xpath('.//td[position() = 1]')
        header_cells = table.xpath('.//tr[position() <= 2]/td')
        # remove br-tags in this table
        br_tags = table.xpath('.//td//br')
        for br in br_tags:
            # insert space before tail text
            br.tail = ' ' + br.tail
            br.drop_tag()
        # iterate leftmost column
        for cell in title_col_cells:
            if cell.text:
                # wrap text into sizeable chunks of max 14 chars
                list_wrap = text_wrap(cell.text, width=14, break_long_words=False)
                # set first chunk to cell text
                cell.text = list_wrap[0]
                # append rest as br-tail
                for tail in reversed(list_wrap[1:]):
                    br_tag = etree.Element('br')
                    br_tag.tail = tail
                    cell.insert(0, br_tag)
        for cell in header_cells:
            if cell.text:
                list_wrap = text_wrap(cell.text, width=3, break_long_words=False)
                cell.text = list_wrap[0]
                for tail in list_wrap[1:]:
                    br_tag = etree.Element('br')
                    br_tag.tail = tail
                    cell.append(br_tag)
    return tree


def span_cleanup(tree):
    """
    removes span and style tags
    :param tree:
    :return: tree
    """
    if gf.flag_is_formatted:
        cleaner = Cleaner(
            remove_tags=['span', 'head'],
            style=True,
            meta=True,
            remove_unknown_tags=False,
            page_structure=False,
            inline_style=True
        )
        return cleaner.clean_html(tree)


# first cleaning of the ABBYY htm before the parsing process really starts
def pre_cleanup(tree):
    """
    This function cleanses the freshly parsed tree and removes unwanted tags and features
    :param tree:
    :return: tree
    """
    for span in tree.xpath('//table//span'):
        span.drop_tag()
    # tree = replace_custom_characters(tree)
    # replace </p><p> in tables with <br>
    for td in tree.xpath('//td[count(p)>1]'):
        for p in td.findall('p')[:-1]:
            br = etree.Element('br')
            br.tail = ' '
            p.append(br)
        # print(html.tostring(td))

    # remove p tags in tables
    for p in tree.xpath('//table//p'):
        p.drop_tag()

    # for t in tree.xpath('//table'):
    #     print(html.tostring(t))

    # change all header hierarchies higher than 3 to 3
    for e in tree.xpath('//*[self::h4 or self::h5 or self::h6]'):
        e.tag = 'h3'

    # remove sup/sub tags from headlines
    for e in tree.xpath('//*[self::h1 or self::h2 or self::h3]/*[self::sup or self::sub]'):
        e.drop_tag()

    # check if report is a fonds report
    if tree.xpath('/html/body/*[starts-with(normalize-space(text()),"Vermögensaufstellung")]'):
        gf.b_fonds_report.set(value=1)
        # remove all multiple occurences of dots and ' )'
        # hacky and not that versatile as of now
        for e in tree.xpath('.//table//*[text()[not(normalize-space()="")]]'):
            if e.text:
                e.text = re.sub(r'\s*?\.{2,}', '', e.text)
                e.text = re.sub(r' \)', ')', e.text)
                e.text = re.sub(r'\)\s*?\.', ')', e.text)
                if len(e):
                    for i in e:
                        if i.tail:
                            i.tail = re.sub(r'\s*?\.{2,}', '', i.tail)
                            i.tail = re.sub(r' \)', ')', i.tail)
                            i.tail = re.sub(r'\)\s*?\.', ')', i.tail)

    # strip all leading and trailing white space in tables
    # for td in tree.xpath('//table//td'):
    #     if td.text is not None:
    #         td.text = td.text.strip()
    #     if len(td):
    #         for tail in td:
    #             if tail.tail is not None:
    #                 tail.tail = tail.tail.strip()

    for txt in tree.xpath('body//*[text()]'):
        if txt.text is not None:
            txt.text = re.sub(r'\s{2,}', ' ', txt.text)
            txt.text = re.sub(r'\n', '', txt.text)
        if txt.tail is not None:
            txt.tail = re.sub(r'\s{2,}', ' ', txt.tail)
            txt.tail = re.sub(r'\n', '', txt.tail)

    # remove li tags in td elements
    for li in tree.xpath('//td/li'):
        li.drop_tag()

    # check if .htm-file is formatted and proceed accordingly
    # execute only if a formatted html file is used (ABBYY export formatted file)
    if tree.xpath('//span'):
        gf.flag_is_formatted = True
        gf.b_span_headings.set(value=1)
        cleaner = Cleaner(
            remove_tags=['a', 'div'],
            style=False,
            meta=False,
            remove_unknown_tags=False,
            page_structure=False,
            inline_style=False,
            safe_attrs_only=False
        )
        tree = cleaner.clean_html(tree)
        print('Found formatted File')
    else:
        cleaner = Cleaner(
            remove_tags=['a', 'head', 'div', 'span'],
            style=True,
            meta=True,
            remove_unknown_tags=False,
            page_structure=False,
            inline_style=True
        )
        tree = cleaner.clean_html(tree)

    # remove sup/sub tags in unordered list candidates and for non footnote candidates
    for sup in tree.xpath('//*[self:: sup or self::sub]'):
        if sup.text is None:
            sup.drop_tag()
        # ToDO: exclude if list of footnote tags [1), 2), ...]
        elif any(list(reg.fullmatch(sup.text) for reg in pt.regUnorderedList)):
            sup.drop_tag()
        elif not any(list(reg.fullmatch(sup.text) for reg in pt.regFootnote)) \
                and not any(re.fullmatch(e, sup.text) for e in pt.lSupElements):
            sup.drop_tag()
    return tree


def post_cleanup(tree, file_path):

    # clean brbr tags
    for h in tree.xpath('//*[self::h1 or self::h2 or self::h3]/br/parent::*'):
        br = h.findall('br')
        if len(br):
            for i in range(len(br)):
                if not br[i].tail and br[i+1].tail:
                    sibling = etree.Element(h.tag)
                    sibling.insert(0, br[i+1])
                    h.addnext(sibling)
                    br[i].drop_tag()
                    br[i+1].drop_tag()
                    i += 1

    # write to new file in source folder
    tree.write(os.path.splitext(file_path)[0] + '_modified.htm', encoding='UTF-8', method='html')

    # clean up user_words.txt
    with open(gf.root_dir + '/data/user_words.txt', 'r', encoding='utf-8') as f:
        sorted_list = '\n'.join(list(dict.fromkeys(f.read().splitlines()))) + '\n'
    with open(gf.root_dir + '/data/user_words.txt', 'w', encoding='utf-8') as f:
        f.write(sorted_list)


def generate_final_tree(arg_list):
    """
    This function generates the final tree element by applying the selected functions of the passed tree
    It also closes the current UI window and calls the post_cleanup function
    :param arg_list: [tree, false_numbers, false_words, new_numbers, new_words]
    :return: None
    """
    tree = arg_list[0]
    false_numbers = arg_list[1]
    false_words = arg_list[2]
    new_numbers = arg_list[3].return_list()
    new_words = arg_list[4].return_list()
    file_path = arg_list[5]
    report_path = os.path.dirname(file_path)
    if gf.b_remove_false_text_breaks.get():
        tree = remove_false_text_breaks(tree)
    if gf.b_span_headings.get():
        tree = set_span_headings(tree)
        tree = span_cleanup(tree)
    if gf.b_merge_tables_vertically.get():
        tree = merge_tables_vertically(tree)
    if gf.b_split_rowspan.get():
        tree = split_rowspan(tree)
    if gf.b_remove_empty_rows.get():
        tree = remove_empty_rows(tree)
    # big_fucking_table()
    # print(false_numbers)
    tree = replace_number_list(tree, new_numbers, false_numbers, report_path)
    # print(false_words)
    tree = replace_word_list(tree, new_words, false_words, report_path)
    if gf.b_set_unordered_lists.get():
        tree = set_unordered_list(tree)
    if gf.b_set_footnotes.get():
        tree = set_footnote_tables(tree)
    if gf.b_set_headers.get():
        tree = set_headers(tree)
    if gf.b_fonds_report.get():
        if gf.b_fix_tsd_separators.get():
            tree = fix_tsd_separators(tree, '.')
        if gf.b_break_fonds_table.get():
            tree = break_fonds_table(tree)

    if gf.b_rename_pics.get():
        tree = rename_pictures(tree, file_path)

    if gf.flag_found_error:
        messagebox.showwarning('Warning', '\n'.join(gf.error_log))

    post_cleanup(tree, file_path)
    gf.error_log.clear()
    gf.flag_found_error = False
    messagebox.showinfo('File generated!', 'File successfully generated!')


####################
# Helper functions #
####################


def get_max_columns(table):
    """
    Returns the passed tables maximum number of columns.
    Also consideres colspans
    :param table:
    :return: int
    """
    # get max number of columns in a row
    firstRow = table.xpath('./tr[1]/td')
    nr_cols = 0
    # if there is a colspan in the row, increase by colspan value
    for td in firstRow:
        if td.get('colspan') is not None:
            nr_cols += int(td.get('colspan'))
        else:
            nr_cols += 1
    return nr_cols


def add_to_error_log(text):
    gf.error_log.append(text)


def is_number(cell):
    """
    takes a HtmlElement or string to evaluate whether it's a valid number, depending on regNumbers pattern list
    :param cell: HtmlElement, String
    :return: bool
    """
    if type(cell) == html.HtmlElement:
        if any(regex.fullmatch(cell.text_content()) for regex in pt.regNumbers):
            return True
    elif type(cell) == str:
        if any(regex.fullmatch(cell) for regex in pt.regNumbers):
            return True
    return False


def remove_br_tag(cell, add_whitespace=False):
    if cell.find('br') is not None:
        for i in cell.findall('br'):
            if add_whitespace:
                i.tail = ' ' + i.tail
            i.drop_tag()
        return True
    else:
        return False

def split_non_consecutive(data):
    """
    splits data list into chunks depending whether the numbers present are consecutive
    :param data:
    :return:
    """
    consec_list = []
    inner_list = []
    for i in range(len(data)):
        if i == 0:
            inner_list = [data[i]]
        elif data[i] == data[i-1] + 1:
            inner_list.append(data[i])
        else:
            consec_list.append(inner_list.copy())
            inner_list.clear()
            inner_list = [data[i]]
    else:
        consec_list.append(inner_list.copy())
    return consec_list



