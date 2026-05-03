#include "trie.h"

Trie::~Trie() {
    clear(root);
}

void Trie::clear(TrieNode *node) {
    for (auto const& pair : node->children) {
        clear(pair.second);
    }
    delete node;
}

void Trie::insert(std::string word) {
    TrieNode *current = root;
    for (char c : word) {
        if (current->children.find(c) == current->children.end()) {
            current->children[c] = new TrieNode();
        }
        current = current->children[c];
    }
    current->isEndOfWord = true;
}

std::vector<std::string> Trie::search(std::string prefix) {
    TrieNode *current = root;
    for (char c : prefix) {
        if (current->children.find(c) == current->children.end()) {
            return {};
        }
        current = current->children[c];
    }

    std::vector<std::string> results;
    collectAllWords(current, prefix, results);
    return results;
}

void Trie::collectAllWords(TrieNode *node, std::string currentPrefix, std::vector<std::string>& results) {
    if (node->isEndOfWord) {
        results.push_back(currentPrefix);
    }

    for (auto const& pair : node->children) {
        collectAllWords(pair.second, currentPrefix + pair.first, results);
    }
}
