import csv


def read(fname, delimiter=',', skip_header=False):
    """
    read loads cell data, column headers and type information for each column
    given a file path to a CSV formatted file.

    All cells have left and right whitespace trimmed.

    All rows MUST be the same length.

    delimiter is the string the separates each field in a row.

    If skip_header is set, then no column headers are read, and column names
    are set to their corresponding indices (as strings).
    """
    names, rows = data(f, delimiter, skip_header)
    types = column_types(names, rows)
    rows = cast(types, names, rows)
    return types, names, rows


def data(fname, delimiter=',', skip_header=False):
    """
    data loads cell data and column headers.

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


def column_types(names, rows):
    """
    column_types infers type information from the columns in rows. Types are
    stored as either a Python type conversion function (str, int or float) or
    as a None value.

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
    for row in rows:
        for i, col in enumerate(row):
            name = names[i]

            # prev_typ is what we believe the type of this column to be up
            # until this point.
            prev_typ = types[name]

            # next_typ is the type of the current cell only. It is compared
            # with prev_typ to determine the type of the overall column as
            # per the conditions specified in this function's documentation.
            next_typ = None

            # A missing value always has type None.
            if len(col) == 0:
                next_typ = None
            else:
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
            if prev_typ == str or next_typ == str:
                types[name] = str
            # A column with floats and ints has type float.
            elif next_typ == float and prev_typ == int:
                types[name] = float
            # A column with missing values and X has type X.
            elif prev_typ is None and next_typ is not None:
                types[name] = next_typ
    return types


def cast(types, names, rows):
    """
    cast type casts all of the values in 'rows' to their corresponding types
    in types.

    The only special case here is missing values or NULL columns. If a value
    is missing or a column has type NULL (i.e., all values are missing), then
    the value is replaced with None, which is Python's version of a NULL value.

    N.B. cast is idempotent. i.e., cast(x) = cast(cast(x)).
    """
    new_rows = []
    for row in rows:
        new_row = []
        for i, col in enumerate(row):
            typ = types[names[i]]
            if (isinstance(col, basestring) and len(col) == 0) \
                    or typ is None or col is None:
                new_row.append(None)
            else:
                new_row.append(typ(col))
        new_rows.append(new_row)
    return new_rows


def convert_missing_cells(types, names, rows, dstr="", dint=0, dfloat=0.0):
    """
    convert_missing_cells changes the values of all NULL cells to the values
    specified by dstr, dint and dfloat. For example, all NULL cells in columns
    with type "string" will be replaced with the value given to dstr.
    """
    new_rows = []
    for row in rows:
        new_row = []
        for i, col in enumerate(row):
            name = names[i]
            typ = types[name]
            if col is None and typ is not None:
                if typ == str:
                    new_row.append(dstr)
                elif typ == int:
                    new_row.append(dint)
                elif typ == float:
                    new_row.append(dfloat)
                else:
                    assert False, "Unknown type: %s" % typ
            else:
                new_row.append(col)
        new_rows.append(new_row)
    return new_rows


def convert_columns(names, rows, **kwargs):
    """
    convert_columns executes converter functions on specific columns, where
    the parameter names for kwargs are the column names, and the parameter
    values are functions of one parameter that return a single value.

    e.g., convert_columns(names, rows, colname=lambda s: s.lower()) would
    convert all values in the column with name 'colname' to lowercase.
    """
    new_rows = []
    for row in rows:
        new_row = []
        for i, col in enumerate(row):
            name = names[i]
            if name in kwargs:
                new_row.append(kwargs[name](col))
            else:
                new_row.append(col)
        new_rows.append(new_row)
    return new_rows


def convert_types(types, names, rows, fstr=None, fint=None, ffloat=None):
    """
    convert_types works just like convert_columns, but on types instead of
    specific columns. This function will likely be more useful, since
    sanitizatiion functions are typically type oriented rather than column
    oriented.

    However, when there are specific kinds of columns that need special
    sanitization, convert_columns should be used.
    """
    new_rows = []
    for row in rows:
        new_row = []
        for i, col in enumerate(row):
            name = names[i]
            typ = types[name]
            if typ == str and fstr is not None:
                new_row.append(fstr(col))
            elif typ == int and fint is not None:
                new_row.append(fint(col))
            elif typ == float and ffloat is not None:
                new_row.append(ffloat(col))
            else:
                new_row.append(col)
        new_rows.append(new_row)
    return new_rows


def column(types, names, rows, colname):
    """
    column returns the column with name "colname", where the column returned
    is a triple of the column type, the column name and a list of cells in the
    column.
    """
    colcells = []
    colname = colname.lower()
    colindex = -1
    for i, name in enumerate(names):
        if name.lower() == colname.lower():
            colindex = i
            break
    assert colindex > -1, 'Column name %s does not exist' % colname

    for row in rows:
        for i, col in enumerate(row):
            if i == colindex:
                colcells.append(col)

    return types[names[colindex]], names[colindex], colcells


def columns(types, names, rows):
    """
    columns returns a list of all columns in the data set, where each column
    is a triple of its type, name and a list of cells in the column.
    """
    colcells = []
    for _ in names:
        colcells.append([])
    for row in rows:
        for i, col in enumerate(row):
            colcells[i].append(col)

    cols = []
    for i, name in enumerate(names):
        cols.append((types[name], name, colcells[i]))
    return cols


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


def print_data_table(types, names, rows):
    """
    print_data_table is a convenience function for pretty-printing the
    data in tabular format, including header names and type annotations.
    """
    padding = 2
    headers = ['%s (%s)' % (name, type_str(types[name])) for name in names]
    maxlens = map(len, headers)
    for row in rows:
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
    for row in rows:
        line = ""
        for i, col in enumerate(row):
            line += padded_cell(i, cell_str(col))
        print line


if __name__ == '__main__':
    # File name.
    f = "sample.csv"

    # Get the initial data from the CSV file, "names" will contain the values
    # of each column in the first row if the optional "skip_header" parameter
    # is not set. If "skip_header" is set, then the column names are the column
    # indices as strings.
    names, rows = data(f)

    # Infers the type of each column. See the function definition for how the
    # types are computed.
    types = column_types(names, rows)

    # Finally, Python's CSV module reads raw data as strings. Thus, arithmetic
    # operations on integer/float columns won't work well. So we use the type
    # information gathered from `column_types` to cast all of the cell data to
    # their appropriate types.
    #
    # Note that this is the place where missing values are inserted as "None".
    # They can be changed with the conversion functions. (Examples follow.)
    rows = cast(types, names, rows)

    # At this point, we've:
    # 1) Loaded the data into a list of column headers and a list of rows.
    # 2) Inferred the type of each column (string, integer, float or None).
    # 3) Casted all cells to their appropriate Python types.
    # These three steps can be accomplished with a single convenience function:
    #
    #   types, names, rows = read(f)
    #
    # I've taken the long approach here so that the process is less opaque.

    # Print the table of raw data.
    print "# Raw data."
    print_data_table(types, names, rows)
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
    rows = convert_missing_cells(types, names, rows)
    print "# Convert missing cells to arbitrary values"
    print_data_table(types, names, rows)
    print '\n'

    # Now that all of the NULL cells have been removed, we are free to run data
    # sanitization functions on the columns of data without worrying about
    # seeing those nasty NULL values. For instance, we might want to make all
    # strings in the 'string1' column be lowercase. We need only to pass a
    # function as an argument, where the function we pass takes a single
    # argument (the cell contents) and returns the new cell contents. In this
    # case, we tell every cell in the `string1` column to be converted using
    # the `str.lower` function.
    rows = convert_columns(names, rows, string1=str.lower)
    print "# Sanitize just one column of data"
    print_data_table(types, names, rows)
    print '\n'

    # The aforementioned function has limited use, since you typically
    # want to be more dynamic than having to give names of columns. Thus, the
    # `convert_types` function allows you to convert cells based on their
    # *type*. That is, instead of making only a selection of columns lowercase,
    # we can specify that *all* string columns should be lowercase.
    rows = convert_types(types, names, rows, fstr=str.lower)
    print "# Sanitize all cells that have type string"
    print_data_table(types, names, rows)
    print '\n'

    # Finally, you can traverse your data set by columns like so:
    for typ, name, cells in columns(types, names, rows):
        print '(%s, %s) [%s]' % (name, typ, ', '.join(map(cell_str, cells)))
    print '\n'

    # Or pick out one column in particular:
    print column(types, names, rows, "mixed")
