from collections import namedtuple
import csv

import numpy as np


Table = namedtuple('Table', ['types', 'names', 'rows'])
Column = namedtuple('Column', ['type', 'name', 'cells'])


def read(fname, delimiter=',', skip_header=False):
    """
    read loads cell data, column headers and type information for each column
    given a file path to a CSV formatted file. A "Table" namedtuple is returned
    with fields "types", "names" and "rows".

    All cells have left and right whitespace trimmed.

    All rows MUST be the same length.

    delimiter is the string the separates each field in a row.

    If skip_header is set, then no column headers are read, and column names
    are set to their corresponding indices (as strings).
    """
    names, rows = _data(fname, delimiter, skip_header)
    types = _column_types(names, rows)

    return cast(Table(types=types, names=names, rows=rows))


def _data(fname, delimiter=',', skip_header=False):
    """
    _data loads cell data and column headers, and returns the names and rows.

    All cells have left and right whitespace trimmed.

    All rows MUST be the same length.

    delimiter and skip_header are described in read.
    """
    names = []
    rows = []
    reader = csv.reader(open(fname), delimiter=delimiter)
    if not skip_header:
        names = map(str.strip, reader.next())

    for i, row in enumerate(reader):
        # If we haven't discovered names from column headers, then name the
        # columns "0", "1", ..., "n-1" where "n" is the number of columns in
        # the first row.
        if len(names) == 0:
            names = map(str, range(0, len(row)))
        assert len(row) == len(names), \
            'The length of row %d is %d, but others rows have length %d' \
            % (i, len(row), len(names))

        rows.append(map(str.strip, row))

    return names, rows


def _column_types(names, rows):
    """
    _column_types infers type information from the columns in rows. Types are
    stored as either a Python type conversion function (str, int or float) or
    as a None value. A dictionary of column names to types is returned.

    A column has type None if and only if all cells in the column are empty.
    (Cells are empty if the length of its value is zero after left and right
    whitespace has been trimmed.)

    A column has type float if and only if all cells in the column are empty,
    integers or floats AND at least one value is a float.

    A column has type int if and only if all cells in the column are empty or
    integers AND at least one value is an int.

    A column has type string in any other case.
    """
    types = dict([(name, None) for name in names])

    for c in xrange(len(names)):
        # prev_typ is what we believe the type of this column to be up
        # until this point.
        prev_typ = None

        # next_typ is the type of the current cell only. It is compared
        # with prev_typ to determine the type of the overall column as
        # per the conditions specified in this function's documentation.
        next_typ = None

        for row in rows:
            col = row[c]

            # A missing value always has type None.
            if len(col) == 0:
                next_typ = None
            # No need to inspect the type if we've already committed to str.
            # (We bail out because it's expensive to inspect types like this.)
            elif prev_typ is not str:
                # The trick here is to attempt type casting from a stirng to
                # an int or a string to a float, and if Python doesn't like it,
                # we try something else.
                try:
                    # We try int first, since any integer can be successfully
                    # converted to a float, but not all floats can converted
                    # to integers.
                    int(col)
                    next_typ = int
                except ValueError:
                    try:
                        # If we can't convert to float, then we must scale back
                        # to a string.
                        float(col)
                        next_typ = float
                    except ValueError:
                        next_typ = str

            # If a column contains a string, the column type is always a
            # string.
            if prev_typ is str or next_typ is str:
                prev_typ = str
            # A column with floats and ints has type float.
            elif next_typ is float and prev_typ is int:
                prev_typ = float
            # A column with missing values and X has type X.
            elif prev_typ is None and next_typ is not None:
                prev_typ = next_typ

        types[names[c]] = prev_typ
    return types


def map_names(table, f):
    """
    new_rows executes f on every column header in the table, with three
    arguments, in order: column type, column index, column name. The result
    of the function is placed in the corresponding header location.

    A new table is returned with the new column names.
    """
    new_names = []
    for i, name in enumerate(table.names):
        new_names.append(f(table.types[name], i, name))
    return table._replace(names=new_names)


def map_data(table, f):
    """
    new_rows executes f on every cell of data with five arguments, in order:
    column type, column name, row index, column index, contents. The result
    of the function is placed in the corresponding cell location.

    A new table is returned with the converted values.
    """
    new_rows = [None] * len(table.rows)
    for r, row in enumerate(table.rows):
        new_row = [None] * len(row)
        for c, col in enumerate(row):
            name = table.names[c]
            typ = table.types[name]
            new_row[c] = f(typ, name, r, c, col)
        new_rows[r] = new_row
    return table._replace(rows=new_rows)


def cast(table):
    """
    cast type casts all of the values in 'rows' to their corresponding types
    in types.

    The only special case here is missing values or NULL columns. If a value
    is missing or a column has type NULL (i.e., all values are missing), then
    the value is replaced with None, which is Python's version of a NULL value.

    N.B. cast is idempotent. i.e., cast(x) = cast(cast(x)).
    """
    def f(typ, name, r, c, cell):
        if (isinstance(cell, basestring) and len(cell) == 0) \
                or typ is None or cell is None:
            return None
        return typ(cell)
    return map_data(table, f)


def convert_missing_cells(table, dstr="", dint=0, dfloat=0.0):
    """
    convert_missing_cells changes the values of all NULL cells to the values
    specified by dstr, dint and dfloat. For example, all NULL cells in columns
    with type "string" will be replaced with the value given to dstr.
    """
    def f(typ, name, r, c, cell):
        if cell is None and typ is not None:
            if typ == str:
                return dstr
            elif typ == int:
                return dint
            elif typ == float:
                return dfloat
            else:
                assert False, "Unknown type: %s" % typ
        return cell
    return map_data(table, f)


def convert_columns(table, **kwargs):
    """
    convert_columns executes converter functions on specific columns, where
    the parameter names for kwargs are the column names, and the parameter
    values are functions of one parameter that return a single value.

    e.g., convert_columns(names, rows, colname=lambda s: s.lower()) would
    convert all values in the column with name 'colname' to lowercase.
    """
    def f(typ, name, r, c, cell):
        if name in kwargs:
            return kwargs[name](cell)
        return cell
    return map_data(table, f)


def convert_types(table, fstr=None, fint=None, ffloat=None):
    """
    convert_types works just like convert_columns, but on types instead of
    specific columns. This function will likely be more useful, since
    sanitizatiion functions are typically type oriented rather than column
    oriented.

    However, when there are specific kinds of columns that need special
    sanitization, convert_columns should be used.
    """
    def f(typ, name, r, c, cell):
        if typ == str and fstr is not None:
            return fstr(cell)
        elif typ == int and fint is not None:
            return fint(cell)
        elif typ == float and ffloat is not None:
            return ffloat(cell)
        return cell
    return map_data(table, f)


def column(table, colname):
    """
    column returns the column with name "colname", where the column returned
    is a triple of the column type, the column name and a NumPy array of
    cells in the column.
    """
    colcells = []
    colname = colname.lower()
    colindex = -1
    for i, name in enumerate(table.names):
        if name.lower() == colname.lower():
            colindex = i
            break
    assert colindex > -1, 'Column name %s does not exist' % colname

    for row in table.rows:
        for i, col in enumerate(row):
            if i == colindex:
                colcells.append(col)

    return Column(type=table.types[table.names[colindex]],
                  name=table.names[colindex],
                  cells=np.array(colcells))


def columns(table):
    """
    columns returns a list of all columns in the data set, where each column
    is a triple of its type, name and a NumPy array of cells in the column.
    """
    colcells = []
    for _ in table.names:
        colcells.append([])
    for row in table.rows:
        for i, col in enumerate(row):
            colcells[i].append(col)

    cols = []
    for i, name in enumerate(table.names):
        col = Column(type=table.types[name],
                     name=name,
                     cells=np.array(colcells[i]))
        cols.append(col)
    return cols


def frequencies(column):
    """
    frequencies returns a dictionary where the keys are unique values in the
    column, and the values correspond to the frequency of each value in the
    column.
    """
    ukeys = np.unique(column.cells)
    bins = np.searchsorted(ukeys, column.cells)
    return dict(zip(ukeys, np.bincount(bins)))


def type_str(typ):
    """
    type_str returns a string representation of a column type.
    """
    if typ is None:
        return "None"
    elif typ is float:
        return "float"
    elif typ is int:
        return "int"
    elif typ is str:
        return "str"
    return "Unknown"


def cell_str(cell_contents):
    """
    cell_str is a convenience function for converting cell contents to a string
    when there are still NULL values.

    N.B. If you choose to work with data while keeping NULL values, you will
    likely need to write more functions similar to this one.
    """
    if cell_contents is None:
        return "NULL"
    return str(cell_contents)


def print_data_table(table):
    """
    print_data_table is a convenience function for pretty-printing the
    data in tabular format, including header names and type annotations.
    """
    padding = 2
    headers = ['%s (%s)' % (n, type_str(table.types[n])) for n in table.names]
    maxlens = map(len, headers)
    for row in table.rows:
        for i, col in enumerate(row):
            maxlens[i] = max(maxlens[i], len(cell_str(col)))

    def padded_cell(i, s):
        spaces = maxlens[i] - len(cell_str(s)) + padding
        return '%s%s' % (cell_str(s), ' ' * spaces)

    line = ""
    for i, name in enumerate(headers):
        line += padded_cell(i, name)
    print line
    print '-' * (sum(map(len, headers)) + len(headers) * padding)
    for row in table.rows:
        line = ""
        for i, col in enumerate(row):
            line += padded_cell(i, cell_str(col))
        print line


if __name__ == '__main__':
    # File name.
    f = "sample.csv"

    table = read(f)

    # Print the table of raw data.
    print "# Raw data."
    print_data_table(table)
    print '\n'

    # Print the table after converting missing values from NULL to concrete
    # values. The benefit here is that NULL values are inherently incomputable.
    # Whenever they get thrown into a computation on the data, they will always
    # provoke a runtime error. This is a Good Thing, because missing values
    # SHOULD be given explicit treatment. Inserting values into missing cells
    # is making an *assumption* about the data, and should never be implied.
    #
    # Thus, `convert_missing_cells` is an EXPLICIT way of throwing away NULL
    # cells. If you view the output from the previous table, and the output of
    # the next table, you'll notice that NULL values have been replaced.
    # (String columns get empty strings, integer columns get 0 and float
    # columns get 0.0.)
    #
    # If you want to change what the missing values are replaced with, you can
    # use the function's optional parameters:
    #
    #   rows = convert_missing_cells(types, names, rows,
    #                                dstr="-9.99", dfloat=-9.99, dint=-9)
    table = convert_missing_cells(table)
    print "# Convert missing cells to arbitrary values"
    print_data_table(table)
    print '\n'

    # Now that all of the NULL cells have been removed, we are free to run data
    # sanitization functions on the columns of data without worrying about
    # seeing those nasty NULL values. For instance, we might want to make all
    # strings in the 'string1' column be lowercase. We need only to pass a
    # function as an argument, where the function we pass takes a single
    # argument (the cell contents) and returns the new cell contents. In this
    # case, we tell every cell in the `string1` column to be converted using
    # the `str.lower` function.
    table = convert_columns(table, string1=str.lower)
    print "# Sanitize just one column of data"
    print_data_table(table)
    print '\n'

    # The aforementioned function has limited use, since you typically
    # want to be more dynamic than having to give names of columns. Thus, the
    # `convert_types` function allows you to convert cells based on their
    # *type*. That is, instead of making only a selection of columns lowercase,
    # we can specify that *all* string columns should be lowercase.
    table = convert_types(table, fstr=str.lower)
    print "# Sanitize all cells that have type string"
    print_data_table(table)
    print '\n'

    # Finally, you can traverse your data set by columns like so:
    for col in columns(table):
        print '(%s, %s) [%s]' \
            % (col.name, col.type, ', '.join(map(cell_str, col.cells)))
    print '\n'

    # Or pick out one column in particular:
    print column(table, "mixed")
