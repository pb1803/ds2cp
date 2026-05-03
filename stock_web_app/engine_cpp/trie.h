#ifndef TRIE_H
#define TRIE_H

#include <string>
#include <vector>
#include <unordered_map>

struct TrieNode {
    std::unordered_map<char, TrieNode*> children;
    bool isEndOfWord;

    TrieNode() : isEndOfWord(false) {}
};

class Trie {
public:
    TrieNode *root;

    Trie() : root(new TrieNode()) {}
    ~Trie();

    void insert(std::string word);
    std::vector<std::string> search(std::string prefix);

private:
    void clear(TrieNode *node);
    void collectAllWords(TrieNode *node, std::string currentPrefix, std::vector<std::string>& results);
};

#endif
